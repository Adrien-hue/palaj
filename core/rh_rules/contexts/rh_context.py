# core/rh_rules/contexts/rh_context.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, Optional, Tuple
from bisect import bisect_left, bisect_right

from core.domain.entities import Agent
from core.domain.enums.day_type import DayType
from core.rh_rules.models.rh_day import RhDay


@dataclass(frozen=True)
class RhContext:
    agent: Agent
    days: Tuple[RhDay, ...]
    window_start: Optional[date] = None
    window_end: Optional[date] = None

    # internal cached indexes (filled in __post_init__)
    _by_date: Dict[date, RhDay] = None  # type: ignore[assignment]
    _dates: Tuple[date, ...] = ()       # aligned with days (same order)

    def __post_init__(self) -> None:
        if not self.days:
            object.__setattr__(self, "_by_date", {})
            object.__setattr__(self, "_dates", ())
            return

        # Ensure sorted
        for i in range(len(self.days) - 1):
            if self.days[i].day_date > self.days[i + 1].day_date:
                raise ValueError("RhContext.days must be sorted by day_date")

        # Build caches once
        by_date: Dict[date, RhDay] = {}
        dates_list: list[date] = []

        for d in self.days:
            # Optional safety: prevent duplicates
            if d.day_date in by_date:
                raise ValueError(f"Duplicate RhDay for date {d.day_date}")
            by_date[d.day_date] = d
            dates_list.append(d.day_date)

        object.__setattr__(self, "_by_date", by_date)
        object.__setattr__(self, "_dates", tuple(dates_list))

    @property
    def by_date(self) -> Dict[date, RhDay]:
        return self._by_date
    
    @property
    def start_date(self) -> Optional[date]:
        return self._dates[0] if self._dates else None

    @property
    def end_date(self) -> Optional[date]:
        return self._dates[-1] if self._dates else None

    @property
    def effective_start(self) -> Optional[date]:
        return self.window_start or self.start_date

    @property
    def effective_end(self) -> Optional[date]:
        return self.window_end or self.end_date

    def get(self, d: date) -> Optional[RhDay]:
        return self._by_date.get(d)

    @staticmethod
    def _is_working(day: RhDay) -> bool:
        return day.day_type in (DayType.WORKING, DayType.ZCOT)

    def previous(self, d: date, *, working_only: bool = False) -> Optional[RhDay]:
        """
        Previous day strictly before d.
        If working_only=True, skip non-working days.
        """
        if not self._dates:
            return None

        idx = bisect_left(self._dates, d) - 1  # last date < d
        while idx >= 0:
            day = self._by_date[self._dates[idx]]
            if not working_only or self._is_working(day):
                return day
            idx -= 1
        return None

    def next(self, d: date, *, working_only: bool = False) -> Optional[RhDay]:
        """
        Next day strictly after d.
        If working_only=True, skip non-working days.
        """
        if not self._dates:
            return None

        idx = bisect_right(self._dates, d)  # first date > d
        while idx < len(self._dates):
            day = self._by_date[self._dates[idx]]
            if not working_only or self._is_working(day):
                return day
            idx += 1
        return None

    def iter_working(self) -> Iterable[RhDay]:
        return (d for d in self.days if self._is_working(d))
