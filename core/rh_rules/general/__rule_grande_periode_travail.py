# core/rh_rules/rule_grande_periode_travail.py
from typing import List, Tuple

from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity
from core.utils.time_helpers import minutes_to_duree_str
from core.domain.contexts.planning_context import PlanningContext
from core.application.services.planning.grande_periode_travail_analyzer import (
    GrandePeriodeTravailAnalyzer,
)


class GrandePeriodeTravailRule(BaseRule):
    """
    Règle RH : vérifie la durée et la charge horaire des Grandes Périodes de Travail (GPT)
    selon l'AE Article 34 :
      - Durée min : 3 jours
      - Durée max : 6 jours
      - Temps max : 48 h
      - Si GPT = 6 jours → RP double obligatoire
    """

    name = "GrandePeriodeTravailRule"
    description = "Durée et charge maximale d'une Grande Période de Travail (GPT)."
    scope = RuleScope.PERIOD

    GPT_MIN_JOURS = 3
    GPT_MAX_JOURS = 6
    GPT_MAX_MINUTES = 48 * 60  # 48 heures en minutes

    def __init__(self, analyzer: GrandePeriodeTravailAnalyzer | None = None):
        self.gpt_service = analyzer or GrandePeriodeTravailAnalyzer()

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        start, end = context.start_date, context.end_date
        if not start or not end:
            return False, [
                self.error(
                    "Impossible de récupérer la date de début ou de fin.",
                    code="GPT_DATES_MISSING",
                )
            ]

        if not context.work_days:
            return True, [
                self.info(
                    "Aucun jour planifié dans le contexte, aucune GPT à analyser.",
                    code="GPT_NO_WORKDAYS",
                )
            ]

        # --- Détection des GPT sur l’ensemble des work_days du contexte ---
        gpts = self.gpt_service.detect_from_workdays(context.work_days)

        if not gpts:
            return True, [
                self.info(
                    "Aucune Grande Période de Travail détectée.",
                    code="GPT_NONE",
                )
            ]

        # Compteurs pour le résumé final
        count_total = len(gpts)
        count_valid = 0
        count_too_short = 0
        count_too_long = 0
        count_too_loaded = 0
        count_requires_rp_double = 0

        # --- Analyse détaillée ---
        for gpt in gpts:
            nb_jours = gpt.nb_jours
            total_minutes = gpt.total_minutes

            # GPT tronquée par les bornes de la période :
            # - commence avant le début du contexte
            # - ou finit après la fin du contexte
            truncated = (gpt.start <= start) or (gpt.end >= end)

            # Trop courte (< 3 jours) → seulement si GPT complète dans la fenêtre
            if nb_jours < self.GPT_MIN_JOURS and not truncated:
                count_too_short += 1
                alerts.append(
                    self.warn(
                        msg=(
                            f"GPT trop courte : {nb_jours} jours "
                            f"(< {self.GPT_MIN_JOURS})."
                        ),
                        jour=gpt.start,
                        code="GPT_TROP_COURTE",
                    )
                )
                # pas considérée comme valide
                continue

            # Trop longue (> 6 jours) → toujours bloquant
            if nb_jours > self.GPT_MAX_JOURS:
                count_too_long += 1
                alerts.append(
                    self.error(
                        msg=(
                            f"GPT trop longue : {nb_jours} jours "
                            f"(> {self.GPT_MAX_JOURS})."
                        ),
                        jour=gpt.end,
                        code="GPT_TROP_LONGUE",
                    )
                )
                # pas valide
                continue

            # Charge horaire excessive (> 48h)
            if total_minutes > self.GPT_MAX_MINUTES:
                count_too_loaded += 1
                alerts.append(
                    self.error(
                        msg=(
                            "Charge horaire excessive : "
                            f"{minutes_to_duree_str(total_minutes)} "
                            f"(> {minutes_to_duree_str(self.GPT_MAX_MINUTES)})."
                        ),
                        jour=gpt.end,
                        code="GPT_CHARGE_TROP_ELEVEE",
                    )
                )

            # GPT = 6 jours → RP double attendu
            if nb_jours == self.GPT_MAX_JOURS:
                count_requires_rp_double += 1
                alerts.append(
                    self.info(
                        msg="GPT de 6 jours → repos double obligatoire.",
                        jour=gpt.end,
                        code="GPT_RP_DOUBLE_ATTENDU",
                    )
                )

            count_valid += 1

        # --- Résumé global (1 seule ligne) ---
        summary = (
            f"{count_total} GPT détectées : "
            f"{count_valid} valides, "
            f"{count_too_short} trop courtes, "
            f"{count_too_long} trop longues, "
            f"{count_too_loaded} > 48h, "
            f"{count_requires_rp_double} nécessitent un RP double."
        )

        alerts.insert(
            0,
            self.info(
                msg=summary,
                code="GPT_SYNTHESE",
            )
        )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
