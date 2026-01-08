# core/rh_rules/analyzers/rest_period_analyzer.py
from __future__ import annotations

from datetime import date
from typing import List

from core.domain.enums.day_type import DayType
from core.rh_rules.models.rest_period import RestPeriod
from core.rh_rules.models.rh_day import RhDay


class RestPeriodAnalyzer:
    """Extract consecutive REST periods from canonical RH days."""

    def detect_from_rh_days(self, rh_days: List[RhDay]) -> List[RestPeriod]:
        if not rh_days:
            return []

        sorted_days = sorted(rh_days, key=lambda d: d.day_date)

        periods: List[RestPeriod] = []
        current_block: List[date] = []

        def close_block() -> None:
            nonlocal current_block
            if current_block:
                periods.append(RestPeriod(days=tuple(current_block)))
                current_block = []

        for d in sorted_days:
            t = d.day_type or DayType.UNKNOWN

            if t == DayType.REST:
                if not current_block:
                    current_block = [d.day_date]
                else:
                    if (d.day_date - current_block[-1]).days == 1:
                        current_block.append(d.day_date)
                    else:
                        close_block()
                        current_block = [d.day_date]
            else:
                close_block()

        close_block()
        return periods