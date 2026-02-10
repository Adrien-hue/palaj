# core/rh_rules/models/rh_day.py
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from core.domain.enums.day_type import DayType
from core.rh_rules.models.rh_interval import RhInterval

@dataclass(frozen=True)
class RhDay:
    agent_id: int
    day_date: date
    day_type: DayType
    intervals: List[RhInterval]
    forfait_minutes: int | None = None

    def is_working(self) -> bool:
        return self.day_type in (DayType.WORKING, DayType.ZCOT)

    def is_rest(self) -> bool:
        return self.day_type in (DayType.LEAVE, DayType.REST)

    def is_absence(self) -> bool:
        return self.day_type == DayType.ABSENT