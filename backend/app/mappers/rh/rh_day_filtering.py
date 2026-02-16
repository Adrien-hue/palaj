from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.models.rh_violation import RhViolation


def filter_violations_for_day(violations: List[RhViolation], day: date) -> List[RhViolation]:
    """
    Keep only violations intersecting 'day'.
    Violations without start_date/end_date are ignored for day view (can't place them).
    """
    out: List[RhViolation] = []
    for v in violations:
        if v.start_date is None or v.end_date is None:
            continue
        if v.start_date <= day <= v.end_date:
            out.append(v)
    return out
