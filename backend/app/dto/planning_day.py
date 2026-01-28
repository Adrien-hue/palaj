# backend/app/dto/planning_day.py
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.app.dto.tranches import TrancheDTO

class PlanningDayDTO(BaseModel):
    day_date: date
    day_type: str
    description: Optional[str] = None
    is_off_shift: bool = False
    tranches: List[TrancheDTO] = Field(default_factory=list)