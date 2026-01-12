# core/rh_rules/day_rule.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from core.rh_rules.base_rule import BaseRule
from core.rh_rules.contexts import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rule_scope import RuleScope
from core.rh_rules.mappers.violation_to_domain_alert import to_domain_alert
from core.utils.domain_alert import DomainAlert


class DayRule(BaseRule, ABC):
    """Rule applied to a single RhDay."""

    scope = RuleScope.DAY

    @abstractmethod
    def check_day(self, context: RhContext, day: RhDay) -> Tuple[bool, List[DomainAlert]]:
        raise NotImplementedError

    def check(self, context: RhContext) -> Tuple[bool, List[DomainAlert]]:
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
        return False, [to_domain_alert(v)]
