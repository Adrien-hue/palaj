from pydantic import BaseModel

from datetime import date
from typing import List

from backend.app.dto.agents import AgentDTO
from backend.app.dto.work_days import WorkDayDTO



class AgentPlanningResponseDTO(BaseModel):
    agent: AgentDTO
    start_date: date
    end_date: date

    work_days: List[WorkDayDTO]