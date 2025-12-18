# db/repositories/poste_repo.py
from sqlalchemy import func
from db import db
from db.models import Poste as PosteModel
from core.domain.entities import Poste as PosteEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper

class PosteRepository(SQLRepository[PosteModel, PosteEntity]):
    def __init__(self):
        super().__init__(db, PosteModel, PosteEntity)

    def get_by_name(self, nom: str) -> PosteEntity | None:
        with self.db.session_scope() as session:
            model = (
                session.query(PosteModel)
                .filter(func.lower(PosteModel.nom) == nom.lower())
                .first()
            )
            return EntityMapper.model_to_entity(model, PosteEntity) if model else None