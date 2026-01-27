from __future__ import annotations

from typing import List, Optional

from sqlalchemy import and_, select, delete

from core.domain.entities.agent_team import AgentTeam as AgentTeamEntity
from core.domain.entities.team import Team as TeamEntity
from db.models.agent import Agent as AgentModel
from db.models.agent_team import AgentTeam as AgentTeamModel
from db.models.team import Team as TeamModel
from core.adapters.entity_mapper import EntityMapper
from db.sql_repository import SQLRepository

from db import db

class AgentTeamSQLRepository(SQLRepository[AgentTeamModel, AgentTeamEntity]):
    def __init__(self):
        super().__init__(db=db, model_class=AgentTeamModel, entity_class=AgentTeamEntity)

    from sqlalchemy import and_

    def delete_for_agent_and_team(self, agent_id: int, team_id: int) -> bool:
        """Supprime l'association agent ↔ équipe. Retourne False si inexistante."""
        with self.db.session_scope() as session:
            model = (
                session.query(AgentTeamModel)
                .filter(
                    and_(
                        AgentTeamModel.agent_id == agent_id,
                        AgentTeamModel.team_id == team_id,
                    )
                )
                .first()
            )

            if not model:
                return False

            session.delete(model)
            # commit géré par session_scope
            return True


    def exists_agent(self, agent_id: int) -> bool:
        with self.db.session_scope() as session:
            row = session.execute(
                select(AgentModel.id)
                .where(AgentModel.id == agent_id)
                .limit(1)
            ).scalar_one_or_none()
            return row is not None


    def exists_team(self, team_id: int) -> bool:
        with self.db.session_scope() as session:
            row = session.execute(
                select(TeamModel.id)
                .where(TeamModel.id == team_id)
                .limit(1)
            ).scalar_one_or_none()
            return row is not None
        
    def get_for_agent_and_team(
        self, agent_id: int, team_id: int
    ) -> Optional[AgentTeamEntity]:
        """Retourne l'association agent ↔ équipe si elle existe."""
        with self.db.session_scope() as session:
            model = (
                session.query(AgentTeamModel)
                .filter(
                    and_(
                        AgentTeamModel.agent_id == agent_id,
                        AgentTeamModel.team_id == team_id,
                    )
                )
                .first()
            )

            return (
                EntityMapper.model_to_entity(model, AgentTeamEntity)
                if model
                else None
            )

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

    def search(
        self,
        agent_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> List[AgentTeamEntity]:
        """
        Search memberships by optional filters.
        - If agent_id is provided, filters by agent_id
        - If team_id is provided, filters by team_id
        - If both are provided, returns at most 1 row in practice (unique constraint)
        """
        with self.db.session_scope() as session:
            q = session.query(AgentTeamModel)

            if agent_id is not None:
                q = q.filter(AgentTeamModel.agent_id == agent_id)

            if team_id is not None:
                q = q.filter(AgentTeamModel.team_id == team_id)

            # stabilité UI
            q = q.order_by(AgentTeamModel.created_at.desc())

            models = q.all()

            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, AgentTeamEntity)) is not None
            ]
