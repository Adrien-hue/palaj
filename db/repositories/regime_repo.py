# db/repositories/regime_repo.py
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

    def find_by_nom(self, nom: str) -> RegimeEntity | None:
        """Recherche un régime par nom (insensible à la casse)."""
        with self.db.session_scope() as session:
            model = session.query(RegimeModel).filter(RegimeModel.nom.ilike(f"%{nom}%")).first()
            return EntityMapper.model_to_entity(model, RegimeEntity)