# db/repositories/agent_day_repo.py
from datetime import date
from typing import List, Optional
from sqlalchemy import exists, func, select
from sqlalchemy.orm import selectinload

from db import db

from db.models import AgentDay as AgentDayModel, AgentDayAssignment as AgentDayAssignmentModel, Tranche as TrancheModel
from core.domain.entities.agent_day import AgentDay as AgentDayEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper

class AgentDayRepository(SQLRepository[AgentDayModel, AgentDayEntity]):
    """
    Repository SQL pour la gestion des journées agent.
    """

    def __init__(self):
        super().__init__(db, AgentDayModel, AgentDayEntity)

    def create(self, entity: AgentDayEntity) -> AgentDayEntity:
        model = EntityMapper.entity_to_model(entity, self.model_class)
        with self.db.session_scope() as session:
            session.add(model)
            session.flush()
            session.refresh(model)
            result = self._model_to_entity(model)
            assert result is not None
            return result
        
    def delete_by_agent_and_date(self, agent_id: int, day_date: date) -> bool:
        """
        Supprime le AgentDay via la clé métier (agent_id, day_date).
        Retourne True si supprimé, False sinon.
        Cascade DB + relationship gèrent agent_day_assignments.
        """
        with self.db.session_scope() as session:
            model = (
                session.query(self.model_class)
                .filter(
                    self.model_class.agent_id == agent_id,
                    self.model_class.day_date == day_date,
                )
                .one_or_none()
            )
            if not model:
                return False
            session.delete(model)
            return True
        
    def delete_empty_days_by_date(self, day_date: date) -> bool:
        """
        Supprime les AgentDay de la date donnée qui n'ont aucun assignment.
        Utile après un rewrite poste/jour.
        """
        with self.db.session_scope() as session:
            deleted = (
                session.query(AgentDayModel)
                .filter(AgentDayModel.day_date == day_date)
                .filter(
                    ~exists().where(AgentDayAssignmentModel.agent_day_id == AgentDayModel.id)
                )
                .delete(synchronize_session=False)
            )
            return bool(deleted)

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
        
    def list_by_agents_and_range(
        self,
        agent_ids: List[int],
        start_date: date,
        end_date: date,
    ) -> List[AgentDayEntity]:
        """
        Bulk read AgentDays (thin) for multiple agents within date range (inclusive).
        - No writes
        - No loading of Agent or Tranche entities
        - tranche_ids loaded via agent_day_assignments
        """
        if not agent_ids:
            return []

        with self.db.session_scope() as session:
            models = (
                session.query(AgentDayModel)
                .filter(
                    AgentDayModel.agent_id.in_(agent_ids),
                    AgentDayModel.day_date >= start_date,
                    AgentDayModel.day_date <= end_date,
                )
                .options(selectinload(AgentDayModel.assignments))
                .order_by(AgentDayModel.agent_id.asc(), AgentDayModel.day_date.asc())
                .all()
            )

            return [self._model_to_entity(m) for m in models]

    def list_by_poste_and_day(self, poste_id: int, day_date: date) -> List[AgentDayEntity]:
        """
        Wrapper convenience: read AgentDays for a single day for a poste.
        """
        return self.list_by_poste_and_range(
            poste_id=poste_id,
            start_date=day_date,
            end_date=day_date,
        )
        
    def list_by_poste_and_range(
        self,
        poste_id: int,
        start_date: date,
        end_date: date,
    ) -> List[AgentDayEntity]:
        """
        Read AgentDays (thin) for all agents that have at least one assignment
        on a tranche of the given poste within the date range (inclusive).
        - No writes
        - No loading of Agent or Tranche entities
        - tranche_ids are loaded through agent_day_assignments
        """
        with self.db.session_scope() as session:
            agent_day_ids_sq = (
                select(AgentDayAssignmentModel.agent_day_id)
                .join(TrancheModel, TrancheModel.id == AgentDayAssignmentModel.tranche_id)
                .join(AgentDayModel, AgentDayModel.id == AgentDayAssignmentModel.agent_day_id)
                .where(
                    TrancheModel.poste_id == poste_id,
                    AgentDayModel.day_date >= start_date,
                    AgentDayModel.day_date <= end_date,
                )
                .distinct()
                .subquery()
            )

            models = (
                session.query(AgentDayModel)
                .filter(AgentDayModel.id.in_(select(agent_day_ids_sq.c.agent_day_id)))
                .options(selectinload(AgentDayModel.assignments))
                .order_by(AgentDayModel.day_date.asc(), AgentDayModel.agent_id.asc())
                .all()
            )

            return [self._model_to_entity(m) for m in models]
        
    def update(self, entity: AgentDayEntity) -> Optional[AgentDayEntity]:
        model = EntityMapper.entity_to_model(entity, self.model_class)
        with self.db.session_scope() as session:
            merged = session.merge(model)
            session.flush()
            session.refresh(merged)
            result = self._model_to_entity(merged)
            assert result is not None
            return result

    def _model_to_entity(self, model: AgentDayModel) -> AgentDayEntity:
        day = EntityMapper.model_to_entity(model, AgentDayEntity)
        if day is None:
            raise ValueError("Failed to map AgentDayModel to AgentDayEntity")

        day.set_tranche_ids([a.tranche_id for a in model.assignments])
        return day
