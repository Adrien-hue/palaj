# db/repositories/agent_day_repo.py
from datetime import date
from typing import List, Optional
from sqlalchemy import func, select
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

            return EntityMapper.model_to_entity(model, AgentDayEntity) if model else None

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
                e for m in models
                if (e := EntityMapper.model_to_entity(m, AgentDayEntity)) is not None
            ]