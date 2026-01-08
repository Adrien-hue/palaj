# core/rh_rules/general/rule_duree_travail.py
from __future__ import annotations

from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.day_rule import DayRule
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.models.rule_scope import RuleScope
from core.rh_rules.utils.rh_night import rh_day_is_nocturne
from core.rh_rules.utils.time_calculations import worked_minutes
from core.utils.domain_alert import DomainAlert
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
        context: PlanningContext,
        work_day: WorkDay,
    ) -> Tuple[bool, List[DomainAlert]]:
        # Build canonical RH day
        rh_day = rh_day_from_workday(context.agent.id, work_day)

        # No work -> nothing to check
        if not rh_day.is_working():
            return True, []

        total_minutes = int(worked_minutes(rh_day))
        is_night = bool(rh_day_is_nocturne(rh_day))

        max_allowed = self.DUREE_MAX_NUIT_MIN if is_night else self.DUREE_MAX_MIN

        alerts: List[DomainAlert] = []

        if total_minutes < self.DUREE_MIN_MIN:
            v = self.error_v(
                code="DUREE_TRAVAIL_MIN_INSUFFISANTE",
                msg=(
                    "Durée de travail insuffisante : "
                    f"{minutes_to_duree_str(total_minutes)} < "
                    f"{minutes_to_duree_str(self.DUREE_MIN_MIN)}"
                ),
                start_date=work_day.jour,
                end_date=work_day.jour,
                meta={
                    "total_minutes": total_minutes,
                    "min_minutes": self.DUREE_MIN_MIN,
                    "is_night": is_night,
                },
            )
            alerts.append(to_domain_alert(v))

        if total_minutes > max_allowed:
            v = self.error_v(
                code=("DUREE_TRAVAIL_MAX_NUIT_DEPASSEE" if is_night else "DUREE_TRAVAIL_MAX_DEPASSEE"),
                msg=(
                    "Durée de travail excessive : "
                    f"{minutes_to_duree_str(total_minutes)} > "
                    f"{minutes_to_duree_str(int(max_allowed))}"
                ),
                start_date=work_day.jour,
                end_date=work_day.jour,
                meta={
                    "total_minutes": total_minutes,
                    "max_minutes": int(max_allowed),
                    "is_night": is_night,
                },
            )
            alerts.append(to_domain_alert(v))

        return len(alerts) == 0, alerts
