from pydantic import BaseModel
from datetime import date

class EtatJourAgentDTO(BaseModel):
    agent_id: int
    jour: date
    type_jour: str
    description: str = ""
