from pydantic import BaseModel
from typing import List, Optional


class AgentDTO(BaseModel):
    id: int
    nom: str
    prenom: str
    code_personnel: Optional[str] = None
    actif: bool = True


class AgentListDTO(BaseModel):
    items: List[AgentDTO]
    total: int
