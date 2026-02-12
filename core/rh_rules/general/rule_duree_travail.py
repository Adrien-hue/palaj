# core/rh_rules/general/rule_duree_travail.py
from __future__ import annotations

from typing import List

from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.day_rule import DayRule
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.utils.rh_night import rh_day_is_nocturne
from core.rh_rules.utils.time_calculations import worked_minutes
from core.utils.time_helpers import minutes_to_duree_str


class DureeTravailRule(DayRule):
    """
    Daily working duration (min/max, with a specific max for night work).
    - Minimum: 5h30 (330 min)
    - Maximum: 10h (600 min)
    - Night maximum: 8h30 (510 min)
    """

    name = "DureeTravailRule"
    description = "Durée journalière de travail (min/max selon travail de nuit)."

    DUREE_MIN_MIN = int(5.5 * 60)       # 330
    DUREE_MAX_MIN = int(10 * 60)        # 600
    DUREE_MAX_NUIT_MIN = int(8.5 * 60)  # 510

    def check_day(
        self,
        context: RhContext,
        day: RhDay,
    ) -> RuleResult:

        # No work -> nothing to check
        if not day.is_working():
            return RuleResult.ok()

        total_minutes = int(worked_minutes(day))
        is_night = bool(rh_day_is_nocturne(day))
        max_allowed = self.DUREE_MAX_NUIT_MIN if is_night else self.DUREE_MAX_MIN

        start_dt = min((i.start for i in day.intervals), default=None)
        end_dt = max((i.end for i in day.intervals), default=None)


        violations: List[RhViolation] = []

        if total_minutes < self.DUREE_MIN_MIN:
            v = self.error_v(
                code="DUREE_TRAVAIL_MIN_INSUFFISANTE",
                msg=(
                    "Durée de travail insuffisante : "
                    f"{minutes_to_duree_str(total_minutes)} < "
                    f"{minutes_to_duree_str(self.DUREE_MIN_MIN)}"
                ),
                start_date=day.day_date,
                end_date=day.day_date,
                meta={
                    "total_minutes": total_minutes,
                    "min_minutes": self.DUREE_MIN_MIN,
                    "is_night": is_night,
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                },
            )
            violations.append(v)

        if total_minutes > max_allowed:
            v = self.error_v(
                code=("DUREE_TRAVAIL_MAX_NUIT_DEPASSEE" if is_night else "DUREE_TRAVAIL_MAX_DEPASSEE"),
                msg=(
                    "Durée de travail excessive : "
                    f"{minutes_to_duree_str(total_minutes)} > "
                    f"{minutes_to_duree_str(int(max_allowed))}"
                ),
                start_date=day.day_date,
                end_date=day.day_date,
                meta={
                    "total_minutes": total_minutes,
                    "max_minutes": int(max_allowed),
                    "is_night": is_night,
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                },
            )
            violations.append(v)

        return RuleResult(violations=violations)
