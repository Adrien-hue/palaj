from pydantic import BaseModel
from datetime import date

class RHValidateAgentRequestDTO(BaseModel):
    agent_id: int
    date_debut: date
    date_fin: date

class RHValidatePosteRequestDTO(BaseModel):
    poste_id: int
    date_debut: date
    date_fin: date

class RHValidatePosteDayRequestDTO(BaseModel):
    poste_id: int
    day: date
    date_debut: date
    date_fin: date