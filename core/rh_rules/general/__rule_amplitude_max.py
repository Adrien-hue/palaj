# core/rh_rules/rule_amplitude_max.py

from typing import List, Tuple

from core.utils.time_helpers import minutes_to_duree_str
from core.utils.domain_alert import DomainAlert
from core.rh_rules.day_rule import DayRule
from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay


class AmplitudeMaxRule(DayRule):
    """
    Vérifie que l'amplitude journalière de travail ne dépasse pas 11h.
    """

    name = "AmplitudeMaxRule"
    description = "Amplitude maximale d'une journée de service."

    MAX_AMPLITUDE_H = 11.0
    MAX_AMPLITUDE_MIN = int(MAX_AMPLITUDE_H * 60)

    def check_day(
        self,
        context: PlanningContext,
        work_day: WorkDay,
    ) -> Tuple[bool, List[DomainAlert]]:

        # Si la journée n'est pas travaillée → rien à contrôler
        if not work_day.is_working():
            return True, []

        alerts: List[DomainAlert] = []

        amplitude = work_day.amplitude_minutes()

        if amplitude > self.MAX_AMPLITUDE_MIN:
            alerts.append(
                self.error(
                    msg=(
                        f"Amplitude journalière trop élevée : "
                        f"{minutes_to_duree_str(amplitude)} "
                        f"(max {minutes_to_duree_str(self.MAX_AMPLITUDE_MIN)})"
                    ),
                    jour=work_day.jour,
                    code="AMPLITUDE_MAX_EXCEEDED",
                )
            )

        return len(alerts) == 0, alerts