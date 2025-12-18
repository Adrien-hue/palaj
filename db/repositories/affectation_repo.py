# db/repositories/affectation_repo.py
from datetime import date
from sqlalchemy import and_
from typing import Optional, List, Tuple

from db import db
from db.models import Affectation as AffectationModel
from db.models import Tranche as TrancheModel
from core.domain.entities.affectation import Affectation as AffectationEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper


class AffectationRepository(SQLRepository[AffectationModel, AffectationEntity]):
    """
    Repository SQL pour la gestion des affectations d'agents aux tranches.
    """

    def __init__(self):
        super().__init__(db, AffectationModel, AffectationEntity)

    def list_for_agent(self, agent_id: int) -> list[AffectationEntity]:
        """Retourne toutes les affectations d'un agent."""
        with self.db.session_scope() as session:
            models = (
                session.query(AffectationModel)
                .filter(AffectationModel.agent_id == agent_id)
                .order_by(AffectationModel.jour.asc())
                .all()
            )
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, AffectationEntity)) is not None
            ]

    def list_for_day(self, jour: date) -> list[AffectationEntity]:
        """Retourne toutes les affectations pour un jour donné."""
        with self.db.session_scope() as session:
            models = session.query(AffectationModel).filter(AffectationModel.jour == jour).all()
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, AffectationEntity)) is not None
            ]
        
    def list_for_poste(
        self,
        poste_id: int,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> list[AffectationEntity]:
        """
        Retourne toutes les affectations d'un poste (via tranche.poste_id),
        optionnellement filtrées sur une plage de dates [start, end].
        """
        with self.db.session_scope() as session:
            q = (
                session.query(AffectationModel)
                .join(AffectationModel.tranche)
                .filter(TrancheModel.poste_id == poste_id)
            )

            if start is not None:
                q = q.filter(AffectationModel.jour >= start)
            if end is not None:
                q = q.filter(AffectationModel.jour <= end)

            models = (
                q.order_by(AffectationModel.jour.asc(), AffectationModel.tranche_id.asc())
                 .all()
            )

            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, AffectationEntity)) is not None
            ]

    def get_for_agent_and_day(self, agent_id: int, jour: date) -> Optional[AffectationEntity]:
        """Récupère l'affectation d'un agent pour une date spécifique."""
        with self.db.session_scope() as session:
            model = (
                session.query(AffectationModel)
                .filter(
                    and_(
                        AffectationModel.agent_id == agent_id,
                        AffectationModel.jour == jour,
                    )
                )
                .first()
            )
            return EntityMapper.model_to_entity(model, AffectationEntity) if model else None

    def upsert(self, entity: AffectationEntity, unique_field: str = "") -> AffectationEntity:
        """
        Crée ou met à jour une affectation selon (agent_id, jour).
        """
        entity_data = EntityMapper.entity_to_dict(entity)

        with self.db.session_scope() as session:
            existing = (
                session.query(AffectationModel)
                .filter(
                    and_(
                        AffectationModel.agent_id == entity_data["agent_id"],
                        AffectationModel.jour == entity_data["jour"],
                    )
                )
                .first()
            )

            if existing:
                EntityMapper.update_model_from_entity(existing, entity)
                model = existing
            else:
                model = AffectationModel(**entity_data)
                session.add(model)

            session.flush()
            session.refresh(model)
            result = EntityMapper.model_to_entity(model, AffectationEntity)
            assert result is not None, "L'upsert doit retourner une entité valide"
            return result

    def get_date_range_for_agent(self, agent_id: int) -> Tuple[Optional[date], Optional[date]]:
        """
        Retourne la première et la dernière date d'affectation pour un agent.
        """
        with self.db.session_scope() as session:
            first_date = (
                session.query(AffectationModel.jour)
                .filter(AffectationModel.agent_id == agent_id)
                .order_by(AffectationModel.jour.asc())
                .limit(1)
                .scalar()
            )
            last_date = (
                session.query(AffectationModel.jour)
                .filter(AffectationModel.agent_id == agent_id)
                .order_by(AffectationModel.jour.desc())
                .limit(1)
                .scalar()
            )
            return first_date, last_date
