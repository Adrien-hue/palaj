# core/rh_rules/general/rule_repos_quotidien.py
from __future__ import annotations

from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.day_rule import DayRule
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_scope import RuleScope
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.utils.rh_bounds import work_bounds
from core.rh_rules.utils.rh_night import rh_day_is_nocturne
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity
from core.utils.time_helpers import minutes_to_duree_str


class ReposQuotidienRule(DayRule):
    """
    Daily rest minimum between two working days.
      - Standard rest: 12h20 (740 minutes)
      - If night work involved: 14h00 (840 minutes)

    This rule is evaluated for each working day, by looking at the rest
    since the previous working day.
    """

    name = "ReposQuotidienRule"
    description = "Vérifie le respect du repos quotidien minimal entre deux jours travaillés."

    REPOS_MIN_STANDARD_MIN = 12 * 60 + 20  # 12h20
    REPOS_MIN_NUIT_MIN = 14 * 60          # 14h00

    def check_day(
        self,
        context: PlanningContext,
        work_day: WorkDay,
    ) -> Tuple[bool, List[DomainAlert]]:

        # Build RH input from current day (no RH logic from WorkDay used)
        curr_rh = rh_day_from_workday(context.agent.id, work_day)

        # Rule applies only to working days
        if curr_rh.is_rest() or not curr_rh.is_working():
            return True, []

        # Legacy: retrieve previous working day via context (still returns WorkDay)
        prev_wd = context.get_previous_working_day(curr_rh.day_date)
        if not prev_wd:
            return True, []

        prev_rh = rh_day_from_workday(context.agent.id, prev_wd)

        # Ensure previous day is actually a working day in RH terms
        if prev_rh.is_rest() or not prev_rh.is_working():
            return True, []

        # Compute datetime bounds of work for both days
        prev_bounds = work_bounds(prev_rh)
        curr_bounds = work_bounds(curr_rh)
        if not prev_bounds or not curr_bounds:
            # No valid intervals → nothing to check
            return True, []

        prev_start_dt, prev_end_dt = prev_bounds
        curr_start_dt, curr_end_dt = curr_bounds

        # Rest minutes between last end and next start
        repos_minutes = int((curr_start_dt - prev_end_dt).total_seconds() / 60)
        if repos_minutes < 0:
            # Should not happen with datetime-based bounds; keep safe fallback
            return True, []

        # Night rest threshold if either day involves night work
        requires_night_rest = rh_day_is_nocturne(prev_rh) or rh_day_is_nocturne(curr_rh)
        repos_min = self.REPOS_MIN_NUIT_MIN if requires_night_rest else self.REPOS_MIN_STANDARD_MIN

        if repos_minutes >= repos_min:
            return True, []

        violation = self.error_v(
            code="REPOS_QUOTIDIEN_INSUFFISANT",
            msg=(
                "Repos quotidien insuffisant : "
                f"{minutes_to_duree_str(repos_minutes)} < {minutes_to_duree_str(repos_min)}"
            ),
            start_date=prev_rh.day_date,
            end_date=curr_rh.day_date,
            start_dt=prev_end_dt,
            end_dt=curr_start_dt,
            meta={
                "rest_min": repos_minutes,
                "min_required": repos_min,
                "night_required": requires_night_rest,
                "prev_day_type": str(prev_rh.day_type),
                "curr_day_type": str(curr_rh.day_type),
                "prev_work_start": prev_start_dt.isoformat(),
                "prev_work_end": prev_end_dt.isoformat(),
                "curr_work_start": curr_start_dt.isoformat(),
                "curr_work_end": curr_end_dt.isoformat(),
            },
        )

        return False, [to_domain_alert(violation)]
