from sqlalchemy import exists

from db import db

from db.models import AgentDayAssignment as AgentDayAssignmentModel
from core.domain.entities import AgentDayAssignment as AgentDayAssignmentEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper

class AgentDayAssignmentRepository(SQLRepository[AgentDayAssignmentModel, AgentDayAssignmentEntity]):
    def __init__(self):
        super().__init__(db, AgentDayAssignmentModel, AgentDayAssignmentEntity)

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
