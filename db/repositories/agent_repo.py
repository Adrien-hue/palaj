# db/repositories/agent_repo.py
from sqlalchemy import func

from db import db
from db.models import Agent as AgentModel
from core.domain.entities.agent import Agent as AgentEntity
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper

class AgentRepository(SQLRepository[AgentModel, AgentEntity]):
    """
    Repository SQL pour la gestion des agents.
    """

    def __init__(self):
        super().__init__(db, AgentModel, AgentEntity)

    def get_by_full_name(self, nom: str, prenom: str) -> AgentEntity | None:
        """
        Recherche un agent par nom et prénom (insensible à la casse).
        Retourne une entité unique ou None si non trouvé.
        """
        with self.db.session_scope() as session:
            model = (
                session.query(AgentModel)
                .filter(
                    func.lower(AgentModel.nom) == nom.lower(),
                    func.lower(AgentModel.prenom) == prenom.lower(),
                )
                .first()
            )
            return EntityMapper.model_to_entity(model, AgentEntity) if model else None
        
    def get_by_id(self, agent_id: int) -> AgentEntity | None:
        """
        Retourne un agent par son identifiant.
        """
        return self.get(agent_id)

    def list_by_regime_id(self, regime_id: int) -> list[AgentEntity]:
        """
        Retourne tous les agents associés à un régime donné.
        """
        with self.db.session_scope() as session:
            models = (
                session.query(AgentModel)
                .filter(AgentModel.regime_id == regime_id)
                .order_by(AgentModel.nom.asc(), AgentModel.prenom.asc())
                .all()
            )

            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, AgentEntity)) is not None
            ]
