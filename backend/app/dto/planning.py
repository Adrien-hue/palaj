from pydantic import BaseModel

from datetime import date
from typing import List

from backend.app.dto.agents import AgentDetailDTO
from backend.app.dto.planning_day import PlanningDayDTO



class AgentPlanningResponseDTO(BaseModel):
    agent: AgentDetailDTO
    start_date: date
    end_date: date

    days: List[PlanningDayDTO]