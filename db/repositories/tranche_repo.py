# db/repositories/tranche_repo.py
from sqlalchemy import func
from db import db
from db.models import Tranche as TrancheModel
from core.domain.entities import Tranche as TrancheEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper


class TrancheRepository(SQLRepository[TrancheModel, TrancheEntity]):
    """
    Repository SQL pour la gestion des tranches horaires.
    """

    def __init__(self):
        super().__init__(db, TrancheModel, TrancheEntity)

    def get_by_id(self, tranche_id: int) -> TrancheEntity | None:
        """
        Récupère une tranche horaire par son ID.
        """
        return self.get(tranche_id)

    def get_by_name(self, nom: str) -> TrancheEntity | None:
        """
        Recherche une ou plusieurs tranches par nom (insensible à la casse).
        Comparaison effectuée côté SQL via LOWER().
        ⚠️ Les accents sont conservés.
        """
        with self.db.session_scope() as session:
            model = (
                session.query(TrancheModel)
                .filter(func.lower(TrancheModel.nom) == nom.lower())
                .first()
            )
            return EntityMapper.model_to_entity(model, TrancheEntity) if model else None

    def list_by_poste_id(self, poste_id: int) -> list[TrancheEntity]:
        """
        Récupère toutes les tranches associées à un poste donné.
        """
        with self.db.session_scope() as session:
            models = (
                session.query(TrancheModel)
                .filter(TrancheModel.poste_id == poste_id)
                .order_by(TrancheModel.heure_debut.asc())
                .all()
            )
            
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, TrancheEntity)) is not None
            ]