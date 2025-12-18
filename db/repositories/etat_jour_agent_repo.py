# db/repositories/etat_jour_agent_repo.py
from datetime import date
from typing import List, Optional
from sqlalchemy import and_

from db import db
from db.models import EtatJourAgent as EtatJourAgentModel
from core.domain.entities.etat_jour_agent import EtatJourAgent as EtatJourAgentEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper


class EtatJourAgentRepository(SQLRepository[EtatJourAgentModel, EtatJourAgentEntity]):
    """
    Repository SQL pour la gestion des états journaliers d'agents (repos, congés, absences, etc.)
    Version adaptée à la nouvelle architecture DDD.
    """

    def __init__(self):
        super().__init__(db, EtatJourAgentModel, EtatJourAgentEntity)

    # =========================================================
    # 🔹 Requêtes de lecture
    # =========================================================
    def get_for_agent_and_day(self, agent_id: int, jour: date) -> Optional[EtatJourAgentEntity]:
        """Récupère l'état d'un agent pour une journée donnée."""
        with self.db.session_scope() as session:
            model = (
                session.query(EtatJourAgentModel)
                .filter(
                    and_(
                        EtatJourAgentModel.agent_id == agent_id,
                        EtatJourAgentModel.jour == jour,
                    )
                )
                .first()
            )
            return EntityMapper.model_to_entity(model, EtatJourAgentEntity) if model else None

    def list_between_dates(
        self,
        date_start: date,
        date_end: date,
    ) -> List[EtatJourAgentEntity]:
        """
        Liste tous les états journaliers entre 2 dates (bornes incluses).
        """
        if date_start > date_end:
            date_start, date_end = date_end, date_start  # sécurité

        with self.db.session_scope() as session:
            models = (
                session.query(EtatJourAgentModel)
                .filter(
                    and_(
                        EtatJourAgentModel.jour >= date_start,
                        EtatJourAgentModel.jour <= date_end,
                    )
                )
                .order_by(
                    EtatJourAgentModel.jour.asc(),
                    EtatJourAgentModel.agent_id.asc(),
                )
                .all()
            )
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, EtatJourAgentEntity)) is not None
            ]

    def list_for_agent(self, agent_id: int) -> List[EtatJourAgentEntity]:
        """Liste tous les états journaliers d’un agent."""
        with self.db.session_scope() as session:
            models = (
                session.query(EtatJourAgentModel)
                .filter(EtatJourAgentModel.agent_id == agent_id)
                .order_by(EtatJourAgentModel.jour.asc())
                .all()
            )
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, EtatJourAgentEntity)) is not None
            ]

    def list_for_agent_between_dates(
        self,
        agent_id: int,
        date_start: date,
        date_end: date,
    ) -> List[EtatJourAgentEntity]:
        """
        Liste les états journaliers d’un agent entre 2 dates (bornes incluses).
        """
        if date_start > date_end:
            date_start, date_end = date_end, date_start  # sécurité simple

        with self.db.session_scope() as session:
            models = (
                session.query(EtatJourAgentModel)
                .filter(
                    and_(
                        EtatJourAgentModel.agent_id == agent_id,
                        EtatJourAgentModel.jour >= date_start,
                        EtatJourAgentModel.jour <= date_end,
                    )
                )
                .order_by(EtatJourAgentModel.jour.asc())
                .all()
            )
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, EtatJourAgentEntity)) is not None
            ]

    def list_for_agent_by_type(self, agent_id: int, *types_jour: str) -> List[EtatJourAgentEntity]:
        """
        Retourne tous les états journaliers correspondant à un ou plusieurs types.
        Ex : repo.list_for_agent_by_type(5, "zcot", "absence")
        """
        with self.db.session_scope() as session:
            models = (
                session.query(EtatJourAgentModel)
                .filter(
                    EtatJourAgentModel.agent_id == agent_id,
                    EtatJourAgentModel.type_jour.in_(types_jour),
                )
                .order_by(EtatJourAgentModel.jour.asc())
                .all()
            )
            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, EtatJourAgentEntity)) is not None
            ]

    # =========================================================
    # 🔹 Upsert spécifique (agent_id + jour)
    # =========================================================
    def upsert(self, entity: EtatJourAgentEntity, unique_field: str = "") -> EtatJourAgentEntity:
        """Crée ou met à jour un état journalier selon (agent_id, jour)."""
        entity_data = EntityMapper.entity_to_dict(entity)

        with self.db.session_scope() as session:
            existing = (
                session.query(EtatJourAgentModel)
                .filter(
                    and_(
                        EtatJourAgentModel.agent_id == entity_data["agent_id"],
                        EtatJourAgentModel.jour == entity_data["jour"],
                    )
                )
                .first()
            )

            if existing:
                EntityMapper.update_model_from_entity(existing, entity)
                model = existing
            else:
                model = EtatJourAgentModel(**entity_data)
                session.add(model)

            session.flush()
            session.refresh(model)
            result = EntityMapper.model_to_entity(model, EtatJourAgentEntity)
            assert result is not None, "L’upsert doit retourner une entité valide"
            return result

    # =========================================================
    # 🔹 Alias pratiques
    # =========================================================
    def list_zcot_for_agent(self, agent_id: int) -> List[EtatJourAgentEntity]:
        return self.list_for_agent_by_type(agent_id, "zcot")

    def list_absences_for_agent(self, agent_id: int) -> List[EtatJourAgentEntity]:
        return self.list_for_agent_by_type(agent_id, "absence")

    def list_conges_for_agent(self, agent_id: int) -> List[EtatJourAgentEntity]:
        return self.list_for_agent_by_type(agent_id, "conge")

    def list_repos_for_agent(self, agent_id: int) -> List[EtatJourAgentEntity]:
        return self.list_for_agent_by_type(agent_id, "repos")

    def list_travail_for_agent(self, agent_id: int) -> List[EtatJourAgentEntity]:
        return self.list_for_agent_by_type(agent_id, "poste")
