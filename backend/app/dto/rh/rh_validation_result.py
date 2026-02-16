from datetime import date
from typing import List
from pydantic import BaseModel

from backend.app.dto.rh_violation import RhViolationDTO


class RhValidationAgentResultDTO(BaseModel):
    is_valid: bool
    violations: List[RhViolationDTO]