from pydantic import BaseModel
from datetime import date

class RHValidateAgentRequestDTO(BaseModel):
    agent_id: int
    date_debut: date
    date_fin: date
