from __future__ import annotations

from typing import List

from sqlalchemy import select, delete

from core.domain.entities.team import Team as TeamEntity
from db.models.agent_team import AgentTeam as AgentTeamModel
from db.models.team import Team as TeamModel
from core.adapters.entity_mapper import EntityMapper
from db.sql_repository import SQLRepository

from db import db

class AgentTeamSQLRepository(SQLRepository[AgentTeamModel, TeamEntity]):
    def __init__(self):
        super().__init__(db=db, model_class=AgentTeamModel, entity_class=TeamEntity)

    def list_teams_for_agent(self, agent_id: int) -> List[TeamEntity]:
        with self.db.session_scope() as session:
            rows = session.execute(
                select(TeamModel)
                .join(AgentTeamModel, AgentTeamModel.team_id == TeamModel.id)
                .where(AgentTeamModel.agent_id == agent_id)
                .order_by(TeamModel.name.asc())
            ).scalars().all()

            return [
                e for m in rows
                if (e := EntityMapper.model_to_entity(m, TeamEntity)) is not None
            ]

    def set_agent_teams(self, agent_id: int, team_ids: set[int]) -> None:
        with self.db.session_scope() as session:
            session.execute(
                delete(AgentTeamModel).where(AgentTeamModel.agent_id == agent_id)
            )
            for tid in team_ids:
                session.add(AgentTeamModel(agent_id=agent_id, team_id=tid))
