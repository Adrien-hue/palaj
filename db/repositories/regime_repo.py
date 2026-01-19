# db/repositories/regime_repo.py
from typing import Optional
from db import db
from db.models import Regime as RegimeModel
from core.domain.entities import Regime as RegimeEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper

class RegimeRepository(SQLRepository[RegimeModel, RegimeEntity]):
    """
    Repository pour la gestion des régimes de travail.
    Version SQLAlchemy — remplace l'ancien BaseRepository JSON.
    """

    def __init__(self):
        super().__init__(db, RegimeModel, RegimeEntity)

    def _default_order_by(self):
        return (RegimeModel.nom.asc(), RegimeModel.id.asc())

    def get_by_id(self, regime_id: int) -> RegimeEntity | None:
        """
        Récupère un régime de travail par son ID.
        """
        return self.get(regime_id)

    def get_by_name(self, nom: str) -> Optional[RegimeEntity]:
        """
        Return a regime by its name, or None if not found.
        """
        with self.db.session_scope() as session:
            model = (
                session.query(RegimeModel)
                .filter(RegimeModel.nom == nom)
                .first()
            )
            return EntityMapper.model_to_entity(model, RegimeEntity) if model else None