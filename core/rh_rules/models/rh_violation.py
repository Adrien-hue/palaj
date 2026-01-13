# core/rh_rules/models/rh_violation.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional

from core.rh_rules.models.rule_scope import RuleScope
from core.utils.severity import Severity

@dataclass(frozen=True)
class RhViolation:
    code: str
    rule_name: str
    severity: Severity
    message: str

    scope: Optional[RuleScope] = None

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    meta: dict[str, Any] = field(default_factory=dict)
