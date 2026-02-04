from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

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

class BulkFailedItem(BaseModel):
    day_date: date
    code: str
    message: str

class AgentPlanningDayBulkPutResponseDTO(BaseModel):
    updated: List[PlanningDayDTO] = Field(default_factory=list)
    failed: List[BulkFailedItem] = Field(default_factory=list)

class AgentPlanningDayBulkPutDTO(BaseModel):
    day_dates: List[date]
    day_type: DayType
    description: Optional[str] = None
    tranche_id: Optional[int] = None

    @field_validator("day_dates")
    @classmethod
    def unique_dates(cls, v: List[date]) -> List[date]:
        if len(v) != len(set(v)):
            raise ValueError("day_dates contains duplicates")
        return v

    @field_validator("tranche_id")
    @classmethod
    def tranche_rules(cls, tranche_id, info):
        day_type = info.data.get("day_type")
        if day_type == DayType.WORKING and tranche_id is None:
            raise ValueError("tranche_id is required when day_type is working")
        if day_type != DayType.WORKING and tranche_id is not None:
            raise ValueError("tranche_id must be null when day_type is not working")
        return tranche_id
