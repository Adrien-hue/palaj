from __future__ import annotations
from typing import List, Protocol, runtime_checkable

from core.domain.entities.team import Team

@runtime_checkable
class AgentTeamRepositoryPort(Protocol):
    def list_teams_for_agent(self, agent_id: int) -> List[Team]: ...
    def set_agent_teams(self, agent_id: int, team_ids: set[int]) -> None: ...
