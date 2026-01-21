from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.app.dto.agents import AgentDTO
from backend.app.dto.postes import PosteDTO
from backend.app.dto.tranches import TrancheDTO


class PostePlanningTrancheDTO(BaseModel):
    tranche: TrancheDTO

    agents: List[AgentDTO] = Field(default_factory=list)


class PostePlanningDayDTO(BaseModel):
    day_date: date
    day_type: str
    description: Optional[str] = None
    is_off_shift: bool = False

    tranches: List[PostePlanningTrancheDTO] = Field(default_factory=list)


class PostePlanningResponseDTO(BaseModel):
    poste: PosteDTO
    start_date: date
    end_date: date

    days: List[PostePlanningDayDTO] = Field(default_factory=list)
