# core/rh_rules/rh_rules_engine.py
from __future__ import annotations

from typing import List

from core.rh_rules.base_rule import BaseRule
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.day_rule import DayRule
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.models.rule_scope import RuleScope

class RHRulesEngine:
    """
    RH-first rules engine.

    - DAY rules: executed for each RhDay in context.days
    - PERIOD rules: executed once for the whole RhContext
    """

    def __init__(self, rules: List[BaseRule] | None = None) -> None:
        self.rules: List[BaseRule] = rules or []

    def register_rule(self, rule: BaseRule) -> None:
        self.rules.append(rule)

    def list_rules(self) -> List[str]:
        return [f"{r.name} ({r.scope.value})" for r in self.rules]

    # -------------------------------------------------
    # Core execution
    # -------------------------------------------------
    def run(self, context: RhContext) -> RuleResult:
        if not context.days:
            return RuleResult.ok()

        violations: list[RhViolation] = []

        # -------------------------
        # DAY rules
        # -------------------------
        day_rules: list[DayRule] = [
            r for r in self.rules if isinstance(r, DayRule)
        ]

        for day in context.days:
            for rule in day_rules:
                if not rule.applies_to(context):
                    continue

                result = rule.check_day(context, day)
                violations.extend(result.violations)

        # -------------------------
        # PERIOD rules
        # -------------------------
        for rule in self.rules:
            if rule.scope is not RuleScope.PERIOD:
                continue
            if not rule.applies_to(context):
                continue

            result = rule.check(context)
            violations.extend(result.violations)

        return RuleResult(violations=violations)
