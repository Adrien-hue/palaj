from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from backend.app.dto.agents import AgentDTO
from backend.app.dto.planning_day import AgentPlanningDayDTO, PlanningDayDTO
from backend.app.dto.team import TeamDTO
from core.domain.enums.day_type import DayType


class TeamAgentPlanningDTO(BaseModel):
    agent: AgentDTO
    days: List[PlanningDayDTO]


class TeamPlanningResponseDTO(BaseModel):
    team: TeamDTO
    start_date: date
    end_date: date
    days: List[date]
    agents: List[TeamAgentPlanningDTO]

class TeamPlanningBulkItemDTO(BaseModel):
    agent_id: int
    day_dates: List[date] = Field(min_length=1)

    @field_validator("day_dates")
    @classmethod
    def unique_dates(cls, v: List[date]) -> List[date]:
        if len(v) != len(set(v)):
            raise ValueError("day_dates contains duplicates")
        return v


class TeamPlanningDayBulkPutDTO(BaseModel):
    items: List[TeamPlanningBulkItemDTO] = Field(min_length=1)

    day_type: DayType
    description: Optional[str] = None
    tranche_id: Optional[int] = None

    @field_validator("tranche_id")
    @classmethod
    def tranche_rules(cls, tranche_id, info):
        day_type = info.data.get("day_type")
        if day_type == DayType.WORKING and tranche_id is None:
            raise ValueError("tranche_id is required when day_type is working")
        if day_type != DayType.WORKING and tranche_id is not None:
            raise ValueError("tranche_id must be null when day_type is not working")
        return tranche_id

    @field_validator("items")
    @classmethod
    def validate_items(cls, items: List[TeamPlanningBulkItemDTO]):
        # agent_id uniques
        agent_ids = [it.agent_id for it in items]
        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError("items contains duplicate agent_id")

        # cellules uniques (agent_id, day_date)
        seen = set()
        for it in items:
            for d in it.day_dates:
                key = (it.agent_id, d)
                if key in seen:
                    raise ValueError("items contains duplicate (agent_id, day_date)")
                seen.add(key)

        return items


class TeamBulkFailedItem(BaseModel):
    agent_id: int
    day_date: date
    code: str
    message: str


class TeamPlanningDayBulkPutResponseDTO(BaseModel):
    updated: List[AgentPlanningDayDTO] = Field(default_factory=list)
    failed: List[TeamBulkFailedItem] = Field(default_factory=list)