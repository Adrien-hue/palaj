from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from core.application.ports.agent_team_repo import AgentTeamRepositoryPort
from core.application.ports.agent_repo import AgentRepositoryPort
from core.application.ports.team_repo import TeamRepositoryPort
from core.application.services.teams.exceptions import NotFoundError
from core.domain.entities.team import Team
from core.domain.entities.agent_team import AgentTeam


class AgentTeamService:
    def __init__(
        self,
        agent_repo: AgentRepositoryPort,
        team_repo: TeamRepositoryPort,
        agent_team_repo: AgentTeamRepositoryPort,
    ):
        self.agent_repo = agent_repo
        self.team_repo = team_repo
        self.agent_team_repo = agent_team_repo

    def create(self, *, agent_id: int, team_id: int) -> AgentTeam:
        # 1) validations existence (pour erreurs claires)
        if not self.agent_team_repo.exists_agent(agent_id):
            raise NotFoundError(code="agent_not_found", details={"agent_id": agent_id})

        if not self.agent_team_repo.exists_team(team_id):
            raise NotFoundError(code="team_not_found", details={"team_id": team_id})

        # 2) idempotence : si déjà lié, on retourne l'existant
        existing = self.agent_team_repo.get_for_agent_and_team(agent_id=agent_id, team_id=team_id)
        if existing is not None:
            return existing

        agent_team = AgentTeam(agent_id=agent_id, team_id=team_id, created_at=datetime.now())

        # 3) création
        return self.agent_team_repo.create(agent_team)
    
    def delete(self, *, agent_id: int, team_id: int) -> bool:
        return self.agent_team_repo.delete_for_agent_and_team(agent_id=agent_id, team_id=team_id)

    def search(self, agent_id: Optional[int] = None, team_id: Optional[int] = None) -> List[AgentTeam]:
        """
        Search qualifications.
        Business rules could be added here later (permissions, scopes, etc.).
        """
        if agent_id is None and team_id is None:
            raise ValueError("At least one filter is required: agent_id or team_id")

        return self.agent_team_repo.search(agent_id=agent_id, team_id=team_id)