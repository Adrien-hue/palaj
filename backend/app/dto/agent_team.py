from typing import List, Set
from pydantic import BaseModel, Field

from .team import TeamDTO

class AgentTeamsUpdateDTO(BaseModel):
    team_ids: Set[int] = Field(default_factory=set)

class AgentTeamsDTO(BaseModel):
    teams: List[TeamDTO]
