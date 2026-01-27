from datetime import datetime
from pydantic import BaseModel

class AgentTeamDTO(BaseModel):
    agent_id: int
    team_id: int
    created_at: datetime
