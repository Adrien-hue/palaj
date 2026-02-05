from datetime import date
from sqlite3 import IntegrityError
from typing import List
from sqlalchemy import exists, select

from db import db

from db.models import AgentDayAssignment as AgentDayAssignmentModel
from db.models import AgentDay as AgentDayModel
from core.domain.entities import AgentDayAssignment as AgentDayAssignmentEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper

class AgentDayAssignmentRepository(SQLRepository[AgentDayAssignmentModel, AgentDayAssignmentEntity]):
    def __init__(self):
        super().__init__(db, AgentDayAssignmentModel, AgentDayAssignmentEntity)

    def create(self, entity: AgentDayAssignmentEntity) -> AgentDayAssignmentEntity:
        model = EntityMapper.entity_to_model(entity, self.model_class)
        with self.db.session_scope() as session:
            session.add(model)
            try:
                session.flush()
                session.refresh(model)
            except IntegrityError:
                # contrainte uq_agent_day_assignments_day_tranche possible
                raise
            result = EntityMapper.model_to_entity(model, self.entity_class)
            assert result is not None, "La création doit retourner une entité valide"
            return result
        
    def delete_by_agent_day_id(self, agent_day_id: int) -> bool:
        """
        Supprime toutes les affectations liées à un agent_day_id.
        Retourne True si au moins une ligne a été supprimée, False sinon.
        """
        with self.db.session_scope() as session:
            deleted = (
                session.query(self.model_class)
                .filter(self.model_class.agent_day_id == agent_day_id)
                .delete(synchronize_session=False)
            )
            return bool(deleted)
        
    def delete_by_date_and_tranche_ids(self, day_date: date, tranche_ids: List[int]) -> bool:
        """
        Supprime tous les assignments sur une date donnée pour un ensemble de tranche_ids.
        Implémentation compatible SQLAlchemy: pas de join() sur un bulk delete.
        """
        if not tranche_ids:
            return False

        with self.db.session_scope() as session:
            agent_day_ids_sq = (
                select(AgentDayModel.id)
                .where(AgentDayModel.day_date == day_date)
                .subquery()
            )

            deleted = (
                session.query(AgentDayAssignmentModel)
                .filter(AgentDayAssignmentModel.agent_day_id.in_(select(agent_day_ids_sq.c.id)))
                .filter(AgentDayAssignmentModel.tranche_id.in_(tranche_ids))
                .delete(synchronize_session=False)
            )
            return bool(deleted)

    def exists_for_tranche(self, tranche_id: int) -> bool:
        """
        True if at least one agent_day_assignment references the tranche.
        Used to block tranche hard delete (strategy 1).
        """
        with self.db.session_scope() as session:
            q = session.query(
                exists().where(AgentDayAssignmentModel.tranche_id == tranche_id)
            )
            return bool(q.scalar())
