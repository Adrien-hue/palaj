from __future__ import annotations

from typing import Optional, List

from sqlalchemy import select

from core.domain.entities.team import Team as TeamEntity
from db.database import SQLiteDatabase
from db.models.team import Team as TeamModel
from db.sql_repository import SQLRepository


class TeamSQLRepository(SQLRepository[TeamModel, TeamEntity]):
    def __init__(self, db: SQLiteDatabase):
        super().__init__(db=db, model_class=TeamModel, entity_class=TeamEntity)

    def _default_order_by(self):
        # Tri stable par nom
        return (TeamModel.name,)

    def get_by_id(self, team_id: int) -> Optional[TeamEntity]:
        return self.get(team_id)

    def get_by_name(self, name: str) -> Optional[TeamEntity]:
        with self.db.session_scope() as session:
            row = session.execute(
                select(TeamModel).where(TeamModel.name == name)
            ).scalar_one_or_none()
            if not row:
                return None
            # mapping via EntityMapper (comme dans la base)
            from core.adapters.entity_mapper import EntityMapper
            return EntityMapper.model_to_entity(row, TeamEntity)

    def get_existing_ids(self, team_ids: set[int]) -> set[int]:
        if not team_ids:
            return set()
        with self.db.session_scope() as session:
            rows = session.execute(
                select(TeamModel.id).where(TeamModel.id.in_(team_ids))
            ).all()
            return {r[0] for r in rows}
