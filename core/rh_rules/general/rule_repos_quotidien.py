# core/rh_rules/general/rule_repos_quotidien.py
from __future__ import annotations

from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.day_rule import DayRule
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.utils.rh_bounds import work_bounds
from core.rh_rules.utils.rh_night import rh_day_is_nocturne
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
        context: RhContext,
        day: RhDay,
    ) -> RuleResult:
        # Rule applies only to working days
        if not day.is_working():
            return RuleResult.ok()

        # Ensure previous day is actually a working day in RH terms
        prev_day = context.previous(day.day_date, working_only=True)
        if not prev_day:
            return RuleResult.ok()

        # Compute datetime bounds of work for both days
        prev_bounds = work_bounds(prev_day)
        curr_bounds = work_bounds(day)
        if not prev_bounds or not curr_bounds:
            # No valid intervals → nothing to check
            return RuleResult.ok()

        prev_start_dt, prev_end_dt = prev_bounds
        curr_start_dt, curr_end_dt = curr_bounds

        # Rest minutes between last end and next start
        repos_minutes = int((curr_start_dt - prev_end_dt).total_seconds() / 60)
        if repos_minutes < 0:
            v = self.error_v(
                code="REPOS_QUOTIDIEN_COHERENCE_DATES",
                msg=(
                    "Incohérence planning : le début du service suivant est avant la fin "
                    "du service précédent (repos négatif)."
                ),
                start_date=prev_day.day_date,
                end_date=day.day_date,
                start_dt=prev_end_dt,
                end_dt=curr_start_dt,
                meta={
                    "rest_min": repos_minutes,
                    "prev_work_start": prev_start_dt.isoformat(),
                    "prev_work_end": prev_end_dt.isoformat(),
                    "curr_work_start": curr_start_dt.isoformat(),
                    "curr_work_end": curr_end_dt.isoformat(),
                },
            )
            return RuleResult(violations=[v])

        # Night rest threshold if either day involves night work
        requires_night_rest = rh_day_is_nocturne(prev_day) or rh_day_is_nocturne(day)
        repos_min = self.REPOS_MIN_NUIT_MIN if requires_night_rest else self.REPOS_MIN_STANDARD_MIN

        if repos_minutes >= repos_min:
            return RuleResult.ok()

        violation = self.error_v(
            code="REPOS_QUOTIDIEN_INSUFFISANT",
            msg=(
                "Repos quotidien insuffisant : "
                f"{minutes_to_duree_str(repos_minutes)} < {minutes_to_duree_str(repos_min)}"
            ),
            start_date=prev_day.day_date,
            end_date=day.day_date,
            start_dt=prev_end_dt,
            end_dt=curr_start_dt,
            meta={
                "rest_min": repos_minutes,
                "min_required": repos_min,
                "night_required": requires_night_rest,
                "prev_day_type": str(prev_day.day_type),
                "curr_day_type": str(day.day_type),
                "prev_work_start": prev_start_dt.isoformat(),
                "prev_work_end": prev_end_dt.isoformat(),
                "curr_work_start": curr_start_dt.isoformat(),
                "curr_work_end": curr_end_dt.isoformat(),
            },
        )

        return RuleResult(violations=[violation])
