from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class AgentTeam:
    agent_id: int
    team_id: int
    created_at: datetime
