from typing import List, Tuple

from core.rh_rules.day_rule import DayRule
from core.utils.domain_alert import DomainAlert
from core.utils.time_helpers import minutes_to_duree_str
from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay

from core.rh_rules.adapters.workday_adapter import rh_day_from_workday
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_scope import RuleScope
from core.rh_rules.utils.rh_bounds import work_bounds
from core.rh_rules.utils.rh_night import rh_day_is_nocturne
from core.utils.severity import Severity


class ReposQuotidienRule(DayRule):
    """
    Minimal daily rest between two working days:
      - standard: 12h20 (740 minutes)
      - night work involved: 14h00 (840 minutes)
    """

    name = "ReposQuotidienRule"
    description = "Vérifie le respect du repos quotidien minimal entre deux jours travaillés."

    REPOS_MIN_STANDARD_MIN = 12 * 60 + 20   # 12h20
    REPOS_MIN_NUIT_MIN = 14 * 60           # 14h00

    def check_day(
        self,
        context: PlanningContext,
        work_day: WorkDay,
    ) -> Tuple[bool, List[DomainAlert]]:

        # Not applicable
        if work_day.is_rest() or not work_day.is_working():
            return True, []

        # Find previous working day (legacy source for now, but we won't use its RH methods)
        prev_wd = context.get_previous_working_day(work_day.jour)
        if not prev_wd or prev_wd.is_rest() or not prev_wd.is_working():
            return True, []

        curr_rh = rh_day_from_workday(context.agent.id, work_day)
        prev_rh = rh_day_from_workday(context.agent.id, prev_wd)

        curr_bounds = work_bounds(curr_rh)
        prev_bounds = work_bounds(prev_rh)
        if not curr_bounds or not prev_bounds:
            return True, []

        curr_start, _ = curr_bounds
        _, prev_end = prev_bounds

        repos_minutes = int((curr_start - prev_end).total_seconds() / 60)
        if repos_minutes < 0:
            # Should not happen with proper datetimes, but keep it safe
            return True, []

        requires_night_rest = rh_day_is_nocturne(prev_rh) or rh_day_is_nocturne(curr_rh)

        repos_min = self.REPOS_MIN_NUIT_MIN if requires_night_rest else self.REPOS_MIN_STANDARD_MIN

        if repos_minutes >= repos_min:
            return True, []

        violation = self.error_v(
            code="REPOS_QUOTIDIEN_INSUFFISANT",
            msg=(
                "Repos quotidien insuffisant : "
                f"{minutes_to_duree_str(repos_minutes)} < "
                f"{minutes_to_duree_str(repos_min)}"
            ),
            start_date=prev_wd.jour,
            end_date=work_day.jour,
            start_dt=prev_end,
            end_dt=curr_start,
            meta={
                "rest_min": repos_minutes,
                "min_required": repos_min,
                "night_required": requires_night_rest,
                "prev_day": str(prev_wd.jour),
                "curr_day": str(work_day.jour),
            },
        )

        return False, [to_domain_alert(violation)]
