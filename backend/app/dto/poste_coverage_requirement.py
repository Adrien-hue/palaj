from typing import Annotated, List

from pydantic import BaseModel, ConfigDict, Field

from backend.app.dto.tranches import TrancheDTO


Weekday = Annotated[int, Field(ge=0, le=6)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class PosteCoverageRequirementDTO(BaseModel):
    weekday: Weekday
    tranche_id: PositiveInt
    required_count: NonNegativeInt = 1

class PosteCoverageDTO(BaseModel):
    poste_id: int
    tranches: List[TrancheDTO]
    requirements: List[PosteCoverageRequirementDTO]

class PosteCoveragePutDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    poste_id: int
    requirements: List[PosteCoverageRequirementDTO]
