from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.day_rule import DayRule
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.utils.time_calculations import amplitude_minutes

from core.utils.time_helpers import minutes_to_duree_str

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
        context: RhContext,
        day: RhDay,
    ) -> RuleResult:

        if not day.is_working():
            return RuleResult.ok()

        amplitude = amplitude_minutes(day)

        if amplitude <= self.MAX_AMPLITUDE_MIN:
            return RuleResult.ok()

        # Build RH violation (front-friendly)
        start_dt = min(i.start for i in day.intervals) if day.intervals else None
        end_dt = max(i.end for i in day.intervals) if day.intervals else None

        violation = self.error_v(
            code="AMPLITUDE_MAX_EXCEEDED",
            msg=(
                f"Amplitude journalière trop élevée : "
                f"{minutes_to_duree_str(amplitude)} "
                f"(max {minutes_to_duree_str(self.MAX_AMPLITUDE_MIN)})"
            ),
            start_date=day.day_date,
            end_date=day.day_date,
            start_dt=start_dt,
            end_dt=end_dt,
            meta={
                "amplitude_min": amplitude,
                "max_min": self.MAX_AMPLITUDE_MIN,
            },
        )

        return RuleResult(violations=[violation])
