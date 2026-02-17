from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from backend.app.dto.rh_violation import RhViolationDTO


class RhValidationAgentResultDTO(BaseModel):
    is_valid: bool
    violations: List[RhViolationDTO]


class RhValidationTeamAgentResultDTO(BaseModel):
    agent_id: int
    result: RhValidationAgentResultDTO

class RhValidationTeamSkippedDTO(BaseModel):
    agent_id: int
    code: str
    details: Optional[Dict[str, Any]] = None

class RhValidationTeamResultDTO(BaseModel):
    results: List[RhValidationTeamAgentResultDTO]
    skipped: List[RhValidationTeamSkippedDTO] = []