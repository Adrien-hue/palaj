# core/rh_rules/rh_rules_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from core.rh_rules.base_rule import BaseRule
from core.rh_rules.contexts import RhContext
from core.rh_rules.day_rule import DayRule
from core.rh_rules.models.rule_scope import RuleScope
from core.utils.domain_alert import DomainAlert
from core.utils.severity import Severity


@dataclass(frozen=True)
class EngineResult:
    is_valid: bool
    alerts: List[DomainAlert]


class RHRulesEngine:
    """
    RH-first rules engine.

    - DAY rules: executed for each RhDay in context.days
    - PERIOD rules: executed once for the whole RhContext
    """

    def __init__(self, rules: List[BaseRule] | None = None):
        self.rules: List[BaseRule] = rules or []

    def register_rule(self, rule: BaseRule) -> None:
        self.rules.append(rule)

    def list_rules(self) -> List[str]:
        return [f"{r.name} ({r.scope.value})" for r in self.rules]

    def run(self, context: RhContext) -> Tuple[bool, List[DomainAlert]]:
        if not context.days:
            return True, []

        all_alerts: List[DomainAlert] = []

        # --- DAY rules
        day_rules: List[DayRule] = [r for r in self.rules if isinstance(r, DayRule)]

        for day in context.days:
            for rule in day_rules:
                if not rule.applies_to(context):
                    continue

                # DayRule exposes check_day; if rule is not a DayRule subclass but uses DAY scope,
                # it should implement check(context, day=...) but we keep it strict here.
                if hasattr(rule, "check_day"):
                    _, alerts = rule.check_day(context, day)  # type: ignore[attr-defined]
                else:
                    # fallback to rule.check(context) if needed (rare)
                    _, alerts = rule.check(context)

                all_alerts.extend(alerts)

        # --- PERIOD rules
        for rule in self.rules:
            if rule.scope is not RuleScope.PERIOD:
                continue
            if not rule.applies_to(context):
                continue

            _, alerts = rule.check(context)
            all_alerts.extend(alerts)

        is_valid = all(a.severity != Severity.ERROR for a in all_alerts)
        return is_valid, all_alerts
