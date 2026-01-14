from pydantic import BaseModel
from datetime import date
from typing import Optional

class QualificationDTO(BaseModel):
    agent_id: int
    poste_id: int
    date_qualification: date

class QualificationCreateDTO(BaseModel):
    agent_id: int
    poste_id: int
    date_qualification: date

class QualificationUpdateDTO(BaseModel):
    date_qualification: Optional[date] = None