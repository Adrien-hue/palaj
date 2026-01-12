# core/rh_rules/year_rule.py
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Tuple

from core.rh_rules.base_rule import BaseRule
from core.rh_rules.contexts import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rule_scope import RuleScope
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.utils.domain_alert import DomainAlert


class YearRule(BaseRule, ABC):
    """
    PERIOD rule (year slicing), RH-first:
      - Uses RhContext.effective_start / effective_end
      - Passes RhDay slices to check_year(...)
    """

    scope = RuleScope.PERIOD

    @abstractmethod
    def check_year(
        self,
        context: RhContext,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        raise NotImplementedError

    def check(self, context: RhContext) -> Tuple[bool, List[DomainAlert]]:
        ctx_start = context.effective_start
        ctx_end = context.effective_end

        if not ctx_start or not ctx_end:
            v = self.error_v(
                code="YEAR_DATES_MISSING",
                msg="Impossible de déterminer les dates de début/fin pour l'analyse annuelle.",
                start_date=context.start_date,
                end_date=context.end_date,
                meta={
                    "window_start": str(context.window_start) if context.window_start else None,
                    "window_end": str(context.window_end) if context.window_end else None,
                },
            )
            return False, [to_domain_alert(v)]

        if not context.days:
            return True, []

        alerts: List[DomainAlert] = []
        is_valid_global = True

        for y in range(ctx_start.year, ctx_end.year + 1):
            year_start = date(y, 1, 1)
            year_end = date(y, 12, 31)

            overlap_start = max(ctx_start, year_start)
            overlap_end = min(ctx_end, year_end)
            if overlap_start > overlap_end:
                continue

            days_year = [d for d in context.days if overlap_start <= d.day_date <= overlap_end]
            is_full = (ctx_start <= year_start) and (ctx_end >= year_end)

            ok, year_alerts = self.check_year(
                context=context,
                year=y,
                year_start=year_start,
                year_end=year_end,
                is_full=is_full,
                days=days_year,
            )

            is_valid_global = is_valid_global and ok
            alerts.extend(year_alerts)

        return is_valid_global, alerts
