from pydantic import BaseModel
from datetime import date
from typing import Optional, Literal

SeverityDTO = Literal["info", "warning", "error", "success"]

class DomainAlertDTO(BaseModel):
    message: str
    severity: SeverityDTO
    jour: Optional[date] = None
    source: Optional[str] = None
    code: Optional[str] = None
