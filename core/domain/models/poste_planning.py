from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from core.domain.entities import Poste, Tranche, Agent
from core.domain.enums.day_type import DayType


@dataclass(frozen=True)
class PostePlanningTranche:
    tranche: Tranche
    agents: List[Agent]


@dataclass(frozen=True)
class PostePlanningDay:
    day_date: date
    day_type: DayType
    description: Optional[str]
    is_off_shift: bool
    tranches: List[PostePlanningTranche]


@dataclass(frozen=True)
class PostePlanning:
    poste: Poste
    start_date: date
    end_date: date
    days: List[PostePlanningDay]
