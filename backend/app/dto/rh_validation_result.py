from typing import List
from pydantic import BaseModel

from backend.app.dto.rh_violation import RhViolationDTO


class RhValidationResultDTO(BaseModel):
    is_valid: bool
    violations: List[RhViolationDTO]