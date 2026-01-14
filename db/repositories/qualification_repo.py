# db/repositories/qualification_repo.py
from sqlalchemy import and_
from sqlalchemy.sql import exists
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

    def delete_for_agent_and_poste(self, agent_id: int, poste_id: int) -> bool:
        with self.db.session_scope() as session:
            model = (
                session.query(QualificationModel)
                .filter(
                    QualificationModel.agent_id == agent_id,
                    QualificationModel.poste_id == poste_id,
                )
                .first()
            )
            if model is None:
                return False

            session.delete(model)
            return True

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

    def is_qualified(self, agent_id: int, poste_id: int) -> bool:
        """Retourne True si l'agent est qualifié pour le poste (qualification existe)."""
        with self.db.session_scope() as session:
            q = (
                session.query(
                    exists().where(
                        and_(
                            QualificationModel.agent_id == agent_id,
                            QualificationModel.poste_id == poste_id,
                        )
                    )
                )
                .scalar()
            )
            return bool(q)

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

    def search(self, agent_id: Optional[int] = None, poste_id: Optional[int] = None) -> List["QualificationEntity"]:
        """
        Search qualifications by optional filters.
        - If agent_id is provided, filters by agent_id
        - If poste_id is provided, filters by poste_id
        - If both are provided, returns at most 1 row in practice (unique constraint)
        """
        with self.db.session_scope() as session:
            q = session.query(QualificationModel)

            if agent_id is not None:
                q = q.filter(QualificationModel.agent_id == agent_id)

            if poste_id is not None:
                q = q.filter(QualificationModel.poste_id == poste_id)

            # Optionnel: order pour stabilité côté UI
            q = q.order_by(QualificationModel.date_qualification.desc())

            models = q.all()

            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, QualificationEntity)) is not None
            ]
        
    from typing import Optional

    def update(self, entity: "QualificationEntity") -> Optional["QualificationEntity"]:
        """
        Update a qualification from an entity using (agent_id, poste_id) as key.
        """
        with self.db.session_scope() as session:
            model = (
                session.query(self.model_class)
                .filter(
                    self.model_class.agent_id == entity.agent_id,
                    self.model_class.poste_id == entity.poste_id,
                )
                .first()
            )
            if not model:
                return None

            EntityMapper.update_model_from_entity(model, entity)
            session.add(model)
            session.flush()
            session.refresh(model)
            return EntityMapper.model_to_entity(model, self.entity_class)


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
