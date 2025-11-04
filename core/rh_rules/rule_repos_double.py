from typing import List, Tuple
from datetime import timedelta

from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.contexts.planning_context import PlanningContext
from core.domain.services.grande_periode_travail_service import GrandePeriodeTravailService
from core.domain.entities import TypeJour


class ReposDoubleRule(BaseRule):
    """
    Règle RH : après une GPT de 6 jours, l'agent doit bénéficier d'au moins 2 jours
    consécutifs de repos complets.
    """

    name = "repos_double"
    description = "Vérifie la présence d'un repos double après une GPT complète de 6 jours."
    scope = RuleScope.PERIOD

    NB_JOURS_REPOS_MIN = 2

    def __init__(self):
        self.gpt_service = GrandePeriodeTravailService()

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        gpts = self.gpt_service.detect_gpts(context)
        if not gpts:
            return True, []

        all_days = sorted(wd.jour for wd in context.work_days)

        for gpt in gpts:
            # On ignore seulement les GPT tronquées à gauche (début partiel)
            if gpt.is_left_truncated:
                continue

            # GPT doit durer 6 jours exactement
            if not gpt.is_maximum():
                continue

            # Vérifier si le planning couvre au moins 2 jours après la fin de la GPT
            days_after_gpt = [d for d in all_days if d > gpt.end]
            if len(days_after_gpt) < self.NB_JOURS_REPOS_MIN:
                # ⚠️ On ne peut pas évaluer, planning trop court
                print(f"[DEBUG] Impossible d’évaluer repos double après GPT ({gpt.start}→{gpt.end}) : contexte trop court")
                continue

            # Récupération des WorkDays après la GPT
            wd_after = [
                wd for wd in context.work_days
                if gpt.end < wd.jour <= gpt.end + timedelta(days=self.NB_JOURS_REPOS_MIN + 1)
            ]

            consecutive_repos = 0
            for wd in wd_after:
                if wd.type() == TypeJour.REPOS:
                    consecutive_repos += 1
                else:
                    break  # série interrompue

            # Vérification du repos minimum
            if consecutive_repos < self.NB_JOURS_REPOS_MIN:
                alerts.append(
                    DomainAlert(
                        message=(
                            f"Repos double manquant après GPT de 6 jours : "
                            f"{consecutive_repos} jour(s) détecté(s), attendu ≥ {self.NB_JOURS_REPOS_MIN}."
                        ),
                        severity=Severity.ERROR,
                        jour=gpt.end + timedelta(days=1),
                        source=self.name,
                    )
                )

        is_valid = all(a.severity not in [Severity.ERROR, Severity.WARNING] for a in alerts)
        return is_valid, alerts
