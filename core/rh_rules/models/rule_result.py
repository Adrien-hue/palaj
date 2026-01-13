# core/rh_rules/models/rule_result.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from core.rh_rules.models.rh_violation import RhViolation
from core.utils.severity import Severity

@dataclass(frozen=True)
class RuleResult:
    violations: List[RhViolation]

    @property
    def is_valid(self) -> bool:
        return all(v.severity != Severity.ERROR for v in self.violations)

    @staticmethod
    def ok() -> "RuleResult":
        return RuleResult(violations=[])