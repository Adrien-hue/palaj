from typing import List, Tuple
from datetime import timedelta

from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.contexts.planning_context import PlanningContext
from core.application.services.planning.grande_periode_travail_analyzer import (
    GrandePeriodeTravailAnalyzer,
)
from core.domain.entities import TypeJour


class ReposDoubleRule(BaseRule):
    """
    Règle RH : après une GPT de 6 jours, l'agent doit bénéficier d'au moins 2 jours
    consécutifs de repos complets.
    """

    name = "ReposDoubleRule"
    description = "Vérifie la présence d'un repos double après une GPT complète de 6 jours."
    scope = RuleScope.PERIOD

    NB_JOURS_REPOS_MIN = 2

    def __init__(self, analyzer: GrandePeriodeTravailAnalyzer | None = None):
        self.gpt_service = analyzer or GrandePeriodeTravailAnalyzer()

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        if not context.work_days:
            return True, []

        # Détection des GPT à partir des work_days du contexte
        gpts = self.gpt_service.detect_from_workdays(
            context.work_days,
            context_start=context.start_date,
            context_end=context.end_date,
        )

        if not gpts:
            return True, []

        # Liste de toutes les dates présentes dans le planning (triées, uniques)
        all_days = sorted({wd.jour for wd in context.work_days})

        for gpt in gpts:
            # On ignore seulement les GPT tronquées à gauche (début partiel)
            if getattr(gpt, "is_left_truncated", False):
                continue

            # GPT doit durer 6 jours exactement (max réglementaire)
            if not gpt.is_maximum():
                continue

            # Vérifier si le planning couvre au moins NB_JOURS_REPOS_MIN jours après la fin de la GPT
            days_after_gpt = [d for d in all_days if d > gpt.end]
            if len(days_after_gpt) < self.NB_JOURS_REPOS_MIN:
                # Contexte trop court pour juger : on ne génère pas d'erreur
                # (comportement identique à l'ancien print de debug, mais silencieux)
                continue

            # Récupération des WorkDays dans la fenêtre juste après la GPT
            wd_after = [
                wd
                for wd in context.work_days
                if gpt.end < wd.jour <= gpt.end + timedelta(days=self.NB_JOURS_REPOS_MIN + 1)
            ]

            consecutive_repos = 0
            for wd in sorted(wd_after, key=lambda w: w.jour):
                if wd.type() == TypeJour.REPOS:
                    consecutive_repos += 1
                else:
                    break  # série interrompue

            # Vérification du repos minimum
            if consecutive_repos < self.NB_JOURS_REPOS_MIN:
                alerts.append(
                    self.error(
                        msg=(
                            "Repos double manquant après GPT de 6 jours : "
                            f"{consecutive_repos} jour(s) détecté(s), "
                            f"attendu ≥ {self.NB_JOURS_REPOS_MIN}."
                        ),
                        jour=gpt.end + timedelta(days=1),
                        code="REPOS_DOUBLE_MANQUANT",
                    )
                )

        # Ici tu avais considéré WARNING comme non-valide aussi.
        # On garde la même logique :
        is_valid = all(a.severity not in (Severity.ERROR, Severity.WARNING) for a in alerts)
        return is_valid, alerts
