# core/rh_rules/analyzers/leave_period_analyzer.py
from __future__ import annotations

from datetime import date
from typing import List

from core.domain.enums.day_type import DayType
from core.rh_rules.models.leave_period import LeavePeriod
from core.rh_rules.models.rh_day import RhDay


class LeavePeriodAnalyzer:
    """
    Detects leave periods from canonical RH days.

    Detection rules:
    - Iterate RH days ordered by date
    - Build blocks of consecutive calendar days where day_type is LEAVE or REST
    - Keep a block only if it contains at least one LEAVE day
    - Any other day_type breaks the block
    """

    def detect_from_rh_days(self, rh_days: List[RhDay]) -> List[LeavePeriod]:
        if not rh_days:
            return []

        sorted_days = sorted(rh_days, key=lambda d: d.day_date)
        periods: List[LeavePeriod] = []

        block: List[date] = []
        leave_count = 0

        def close() -> None:
            nonlocal block, leave_count
            if block and leave_count > 0:
                periods.append(LeavePeriod(days=tuple(block), leave_days=leave_count))
            block = []
            leave_count = 0

        def start(day: date, is_leave: bool) -> None:
            nonlocal block, leave_count
            block = [day]
            leave_count = 1 if is_leave else 0

        for d in sorted_days:
            t = d.day_type or DayType.UNKNOWN

            if t in (DayType.LEAVE, DayType.REST):
                if not block:
                    start(d.day_date, t == DayType.LEAVE)
                    continue

                if (d.day_date - block[-1]).days == 1:
                    block.append(d.day_date)
                    if t == DayType.LEAVE:
                        leave_count += 1
                else:
                    close()
                    start(d.day_date, t == DayType.LEAVE)
            else:
                close()

        close()
        return periods