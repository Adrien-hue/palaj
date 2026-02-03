from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from core.domain.entities.tranche import Tranche
from core.domain.enums.day_type import DayType


@dataclass(frozen=True)
class PlanningDay:
    day_date: date
    day_type: str
    description: Optional[str]
    is_off_shift: bool
    tranches: List[Tranche]

    @property
    def day_type_enum(self) -> DayType:
        try:
            return DayType(self.day_type)
        except ValueError:
            return DayType.UNKNOWN