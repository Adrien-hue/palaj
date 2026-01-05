from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from core.domain.entities.tranche import Tranche
from core.domain.enums.day_type import DayType


@dataclass(frozen=True)
class PlanningDay:
    day_date: date
    day_type: DayType
    description: Optional[str]
    is_off_shift: bool
    tranches: List[Tranche]
