from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel

from backend.app.dto.agents import AgentDTO
from backend.app.dto.planning_day import PlanningDayDTO
from backend.app.dto.team import TeamDTO


class TeamAgentPlanningDTO(BaseModel):
    agent: AgentDTO
    days: List[PlanningDayDTO]


class TeamPlanningResponseDTO(BaseModel):
    team: TeamDTO
    start_date: date
    end_date: date
    days: List[date]
    agents: List[TeamAgentPlanningDTO]
