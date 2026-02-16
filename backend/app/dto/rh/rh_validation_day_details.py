from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel

from backend.app.dto.rh.rh_validation_result import RhViolationDTO


class RhValidationPosteDayAgentDTO(BaseModel):
    agent_id: int
    is_valid: bool

    errors_count: int
    warnings_count: int
    infos_count: int

    violations: List[RhViolationDTO]


class RhValidationPosteDayDetailsDTO(BaseModel):
    poste_id: int
    date: date
    profile: str
    eligible_agents_count: int
    agents: List[RhValidationPosteDayAgentDTO]
