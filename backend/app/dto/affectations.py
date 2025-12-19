from pydantic import BaseModel
from datetime import date

class AffectationDTO(BaseModel):
    agent_id: int
    tranche_id: int
    jour: date
