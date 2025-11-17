# db/repositories/qualification_repo.py
from sqlalchemy import and_
from typing import Optional, List

from db import db
from db.models import Qualification as QualificationModel
from core.domain.entities.qualification import Qualification as QualificationEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper


class QualificationRepository(SQLRepository[QualificationModel, QualificationEntity]):
    """
    Repository SQL pour la gestion des qualifications.
    (Lien entre agent et poste, avec date d’attribution éventuelle)
    """

    def __init__(self):
        super().__init__(db, QualificationModel, QualificationEntity)

    def list_for_agent(self, agent_id: int) -> list[QualificationEntity]:
        """Retourne toutes les qualifications d’un agent."""
        with self.db.session_scope() as session:
            models = (
                session.query(QualificationModel)
                .filter(QualificationModel.agent_id == agent_id)
                .order_by(QualificationModel.date_qualification.asc().nulls_last())
                .all()
            )
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, QualificationEntity)) is not None
            ]

    def list_for_poste(self, poste_id: int) -> list[QualificationEntity]:
        """Retourne toutes les qualifications pour un poste donné."""
        with self.db.session_scope() as session:
            models = (
                session.query(QualificationModel)
                .filter(QualificationModel.poste_id == poste_id)
                .order_by(QualificationModel.date_qualification.asc().nulls_last())
                .all()
            )
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, QualificationEntity)) is not None
            ]

    def get_for_agent_and_poste(
        self, agent_id: int, poste_id: int
    ) -> Optional[QualificationEntity]:
        """Retourne la qualification d’un agent pour un poste donné."""
        with self.db.session_scope() as session:
            model = (
                session.query(QualificationModel)
                .filter(
                    and_(
                        QualificationModel.agent_id == agent_id,
                        QualificationModel.poste_id == poste_id,
                    )
                )
                .first()
            )
            return EntityMapper.model_to_entity(model, QualificationEntity) if model else None

    def upsert(self, entity: QualificationEntity, unique_field: str = "") -> QualificationEntity:
        """Crée ou met à jour une qualification selon (agent_id, poste_id)."""
        entity_data = EntityMapper.entity_to_dict(entity)

        with self.db.session_scope() as session:
            existing = (
                session.query(QualificationModel)
                .filter(
                    and_(
                        QualificationModel.agent_id == entity_data["agent_id"],
                        QualificationModel.poste_id == entity_data["poste_id"],
                    )
                )
                .first()
            )

            if existing:
                # Mise à jour si déjà existante
                for key, value in entity_data.items():
                    setattr(existing, key, value)

                if not entity_data.get("agent_id") or not entity_data.get("poste_id"):
                    raise ValueError("agent_id et poste_id sont requis pour une qualification")
                
                session.flush()
                session.refresh(existing)
                model = existing
            else:
                # Création si nouvelle
                model = QualificationModel(**entity_data)

                if not entity_data.get("agent_id") or not entity_data.get("poste_id"):
                    raise ValueError("agent_id et poste_id sont requis pour une qualification")

                session.add(model)
                session.flush()
                session.refresh(model)

            result = EntityMapper.model_to_entity(model, QualificationEntity)
            assert result is not None, "L'upsert doit retourner une entité valide"
            return result
