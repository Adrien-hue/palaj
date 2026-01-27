from __future__ import annotations

from typing import List

from core.application.ports.agent_team_repo import AgentTeamRepositoryPort
from core.application.ports.agent_repo import AgentRepositoryPort
from core.application.ports.team_repo import TeamRepositoryPort
from core.application.services.teams.exceptions import NotFoundError
from core.domain.entities.team import Team


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

    def list_teams_for_agent(self, agent_id: int) -> List[Team]:
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(code="agent_not_found", details={"agent_id": agent_id})
        return self.agent_team_repo.list_teams_for_agent(agent_id)

    def set_agent_teams(self, agent_id: int, team_ids: set[int]) -> None:
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise NotFoundError(code="agent_not_found", details={"agent_id": agent_id})

        existing = self.team_repo.get_existing_ids(team_ids)
        missing = team_ids - existing
        if missing:
            raise NotFoundError(code="team_not_found", details={"missing_team_ids": sorted(missing)})

        self.agent_team_repo.set_agent_teams(agent_id, team_ids)
