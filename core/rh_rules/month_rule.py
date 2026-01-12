# core/rh_rules/month_rule.py
from __future__ import annotations

from abc import ABC, abstractmethod
from calendar import monthrange
from datetime import date
from typing import Iterable, List

from core.rh_rules.base_rule import BaseRule
from core.rh_rules.contexts import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.models.rule_scope import RuleScope


class MonthRule(BaseRule, ABC):
    """
    PERIOD rule split by civil months (RH-first).

    - splits RhContext effective window into (year, month)
    - for each month: computes overlap
    - slices RhDay within overlap
    - determines if the civil month is fully covered by the effective window
    - delegates to check_month(...)
    """

    scope = RuleScope.PERIOD

    @abstractmethod
    def check_month(
        self,
        context: RhContext,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        raise NotImplementedError

    def _iter_months_in_window(self, start: date, end: date) -> Iterable[tuple[int, int]]:
        year, month = start.year, start.month
        while (year, month) <= (end.year, end.month):
            yield year, month
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1

    def check(self, context: RhContext) -> RuleResult:
        start = context.effective_start
        end = context.effective_end

        if not start or not end:
            v = self.error_v(
                code="MONTH_NO_DATES",
                msg="Impossible de déterminer les bornes de la période pour une règle mensuelle.",
                start_date=context.start_date,
                end_date=context.end_date,
                meta={
                    "window_start": str(context.window_start) if context.window_start else None,
                    "window_end": str(context.window_end) if context.window_end else None,
                },
            )
            return RuleResult(violations=[v])

        if not context.days:
            return RuleResult(violations=[])

        violations: list[RhViolation] = []

        for year, month in self._iter_months_in_window(start, end):
            month_start = date(year, month, 1)
            month_end = date(year, month, monthrange(year, month)[1])

            overlap_start = max(start, month_start)
            overlap_end = min(end, month_end)
            if overlap_start > overlap_end:
                continue

            days_month = [d for d in context.days if overlap_start <= d.day_date <= overlap_end]
            is_full = (start <= month_start) and (end >= month_end)

            result = self.check_month(
                context=context,
                year=year,
                month=month,
                month_start=month_start,
                month_end=month_end,
                is_full=is_full,
                days=days_month,
            )

            violations.extend(result.violations)

        return RuleResult(violations=violations)