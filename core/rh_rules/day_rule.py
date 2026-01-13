# core/rh_rules/day_rule.py
from __future__ import annotations

from abc import ABC, abstractmethod

from core.rh_rules.base_rule import BaseRule
from core.rh_rules.contexts import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.models.rule_scope import RuleScope


class DayRule(BaseRule, ABC):
    """Rule applied to a single RhDay."""

    scope = RuleScope.DAY

    @abstractmethod
    def check_day(self, context: RhContext, day: RhDay) -> RuleResult:
        raise NotImplementedError

    def check(self, context: RhContext) -> RuleResult:
        """
        Guard rail: engine must call check_day(ctx, day), not check(ctx).
        We still provide a deterministic, front-friendly violation.
        """
        v = self.error_v(
            code="DAY_RULE_INVALID_CALL",
            msg="DayRule.check() should not be called directly. Engine must call check_day(ctx, day).",
            start_date=context.effective_start,
            end_date=context.effective_end,
            meta={"hint": "Use check_day(context, day)"},
        )
        return RuleResult(violations=[v])
