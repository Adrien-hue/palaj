# core/rh_rules/rule_grande_periode_travail.py
from typing import List, Tuple
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity
from core.utils.time_helpers import minutes_to_duree_str
from core.domain.contexts.planning_context import PlanningContext
from core.application.services.planning.grande_periode_travail_analyzer import GrandePeriodeTravailAnalyzer


class GrandePeriodeTravailRule(BaseRule):
    """
    Règle RH : vérifie la durée et la charge horaire des Grandes Périodes de Travail (GPT)
    selon l'AE Article 34 :
      - Durée min : 3 jours
      - Durée max : 6 jours
      - Temps max : 48 h
      - Si GPT = 6 jours → RP double obligatoire
    """

    name = "grande_periode_travail"
    description = "Durée et charge maximale d'une Grande Période de Travail (GPT)."
    scope = RuleScope.PERIOD

    GPT_MIN_JOURS = 3
    GPT_MAX_JOURS = 6
    GPT_MAX_MINUTES = 48 * 60  # 48 heures en minutes

    def __init__(self):
        self.gpt_service = GrandePeriodeTravailAnalyzer()

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        start = context.start_date
        end = context.end_date

        if not start or not end:
            alerts.append(
                DomainAlert(
                    "Impossible de récupérer les dates de début ou de fin du context.",
                    Severity.ERROR,
                    source=self.name,
                )
            )

            return False, alerts

        # 🧩 Détection des GPT directement à partir du contexte
        gpts = self.gpt_service.detect(context)

        if not gpts:
            return True, []

        for gpt in gpts:
            nb_jours = gpt.nb_jours
            total_minutes = gpt.total_minutes

            is_left_truncated = gpt.start <= start
            is_right_truncated = gpt.end >= end
            is_truncated = is_left_truncated or is_right_truncated

            # --- GPT trop courte (<3 jours)
            if nb_jours < self.GPT_MIN_JOURS and not is_truncated:
                alerts.append(
                    DomainAlert(
                        f"GPT trop courte : {nb_jours} jours (< {self.GPT_MIN_JOURS}).",
                        Severity.WARNING,
                        jour=gpt.start,
                        source=self.name,
                    )
                )

            # --- GPT trop longue (>6 jours)
            if nb_jours > self.GPT_MAX_JOURS:
                alerts.append(
                    DomainAlert(
                        f"GPT trop longue : {nb_jours} jours (> {self.GPT_MAX_JOURS}).",
                        Severity.ERROR,
                        jour=gpt.end,
                        source=self.name,
                    )
                )

            # --- Trop d'heures (>48h)
            if total_minutes > self.GPT_MAX_MINUTES:
                alerts.append(
                    DomainAlert(
                        f"Charge horaire excessive : {minutes_to_duree_str(total_minutes)} (> {minutes_to_duree_str(self.GPT_MAX_MINUTES)}).",
                        Severity.ERROR,
                        jour=gpt.end,
                        source=self.name,
                    )
                )

            # --- GPT = 6 jours → repos double attendu
            if nb_jours == self.GPT_MAX_JOURS:
                alerts.append(
                    DomainAlert(
                        "GPT de 6 jours détectée → Repos double obligatoire.",
                        Severity.INFO,
                        jour=gpt.end,
                        source=self.name,
                    )
                )

            alerts.append(
                DomainAlert(
                    message=(
                        f"GPT détectée : {gpt.start:%d/%m/%Y} → {gpt.end:%d/%m/%Y} "
                        f"({nb_jours}j, {minutes_to_duree_str(total_minutes)}) {gpt.category()}"
                    ),
                    severity=Severity.INFO,
                    jour=gpt.start,
                    source=self.name,
                )
            )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts