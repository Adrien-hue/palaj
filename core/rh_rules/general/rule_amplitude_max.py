from typing import List, Tuple

from core.utils.time_helpers import minutes_to_duree_str
from core.utils.domain_alert import DomainAlert
from core.rh_rules.day_rule import DayRule
from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay

from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.utils.time_calculations import amplitude_minutes


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

        rh_day = rh_day_from_workday(context.agent.id, work_day)
        amplitude = amplitude_minutes(rh_day)

        if amplitude <= self.MAX_AMPLITUDE_MIN:
            return True, []

        # Build RH violation (front-friendly)
        start_dt = min(i.start for i in rh_day.intervals) if rh_day.intervals else None
        end_dt = max(i.end for i in rh_day.intervals) if rh_day.intervals else None

        violation = self.error_v(
            code="AMPLITUDE_MAX_EXCEEDED",
            msg=(
                f"Amplitude journalière trop élevée : "
                f"{minutes_to_duree_str(amplitude)} "
                f"(max {minutes_to_duree_str(self.MAX_AMPLITUDE_MIN)})"
            ),
            start_date=work_day.jour,
            end_date=work_day.jour,
            start_dt=start_dt,
            end_dt=end_dt,
            meta={
                "amplitude_min": amplitude,
                "max_min": self.MAX_AMPLITUDE_MIN,
            },
        )

        alert = to_domain_alert(violation)
        return False, [alert]
