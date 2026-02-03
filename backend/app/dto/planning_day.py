# backend/app/dto/planning_day.py
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.dto.tranches import TrancheDTO

from core.domain.enums.day_type import DayType

class PlanningDayDTO(BaseModel):
    day_date: date
    day_type: str
    description: Optional[str] = None
    is_off_shift: bool = False
    tranches: List[TrancheDTO] = Field(default_factory=list)

class PlanningDayPutDTO(BaseModel):
    day_type: DayType
    description: Optional[str] = None
    tranche_id: Optional[int] = Field(default=None, description="Only used when day_type=WORKING")
