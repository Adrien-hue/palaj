# db/repositories/agent_day_repo.py
from datetime import date
from typing import List, Optional
from sqlalchemy import exists, func, select
from sqlalchemy.orm import selectinload

from db import db

from db.models import AgentDay as AgentDayModel
from core.domain.entities.agent_day import AgentDay as AgentDayEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper

class AgentDayRepository(SQLRepository[AgentDayModel, AgentDayEntity]):
    """
    Repository SQL pour la gestion des journées agent.
    """

    def __init__(self):
        super().__init__(db, AgentDayModel, AgentDayEntity)

    def exists_for_agent(self, agent_id: int) -> bool:
        """
        Returns True if at least one AgentDay exists for the given agent_id.
        Used to block hard delete (strategy 1).
        """
        with self.db.session_scope() as session:
            q = session.query(
                exists().where(AgentDayModel.agent_id == agent_id)
            )
            return bool(q.scalar())

    def get_by_agent_and_date(self, agent_id: int, day_date: date) -> Optional[AgentDayEntity]:
        """
        Read a single AgentDay (thin) for one agent at a specific date.
        - No writes
        - No loading of Agent or Tranche entities
        - tranche_ids are loaded through agent_day_assignments
        """
        with self.db.session_scope() as session:
            model = (
                session.query(AgentDayModel)
                .filter(
                    AgentDayModel.agent_id == agent_id,
                    AgentDayModel.day_date == day_date,
                )
                .options(selectinload(AgentDayModel.assignments))
                .first()
            )

            return self._model_to_entity(model) if model else None

    def list_by_agent_and_range(
        self,
        agent_id: int,
        start_date: date,
        end_date: date,
    ) -> List[AgentDayEntity]:
        """
        Read AgentDays (thin) for one agent within a date range (inclusive).
        - No writes
        - No loading of Agent or Tranche entities
        - tranche_ids are loaded through agent_day_assignments
        """
        with self.db.session_scope() as session:
            models = (
                session.query(AgentDayModel)
                .filter(
                    AgentDayModel.agent_id == agent_id,
                    AgentDayModel.day_date >= start_date,
                    AgentDayModel.day_date <= end_date,
                )
                .options(selectinload(AgentDayModel.assignments))
                .order_by(AgentDayModel.day_date.asc())
                .all()
            )

            return [
                self._model_to_entity(m)
                for m in models
            ]

    def _model_to_entity(self, model: AgentDayModel) -> AgentDayEntity:
        day = EntityMapper.model_to_entity(model, AgentDayEntity)
        if day is None:
            raise ValueError("Failed to map AgentDayModel to AgentDayEntity")

        day.set_tranche_ids([a.tranche_id for a in model.assignments])
        return day
