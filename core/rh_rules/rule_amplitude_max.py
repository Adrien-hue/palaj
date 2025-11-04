# core/rh_rules/rule_amplitude_max.py
from typing import List, Tuple

from core.utils.time_helpers import minutes_to_duree_str
from core.utils.domain_alert import DomainAlert, Severity
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.domain.contexts.planning_context import PlanningContext


class AmplitudeMaxRule(BaseRule):
    """
    Vérifie que l'amplitude journalière de travail ne dépasse pas 11h.
    """

    name = "amplitude_max"
    description = "Amplitude maximale de 11 heures de travail par jour."
    scope = RuleScope.DAY

    MAX_AMPLITUDE_H = 11.0
    MAX_AMPLITUDE_MIN = int(MAX_AMPLITUDE_H * 60)

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        jour = context.date_reference

        if not jour:
            return True, []

        # 🔹 Utilisation directe du contexte
        amplitude = context.get_amplitude_for_day(jour)
        if amplitude == 0:
            return True, []

        # 🔹 Vérification du seuil
        if amplitude > self.MAX_AMPLITUDE_MIN:
            alerts.append(
                DomainAlert(
                    message=f"Amplitude journalière trop élevée : {minutes_to_duree_str(amplitude)} (max {minutes_to_duree_str(self.MAX_AMPLITUDE_MIN)})",
                    severity=Severity.ERROR,
                    jour=jour,
                    source=self.name,
                )
            )

        return len(alerts) == 0, alerts