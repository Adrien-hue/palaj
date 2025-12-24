# core/application/service/agent_service.py
from typing import Any, List, Optional

from core.application.ports import (
    AffectationRepositoryPort,
    AgentRepositoryPort,
    EtatJourAgentRepositoryPort,
    QualificationRepositoryPort,
    RegimeRepositoryPort,
)
from core.domain.entities import Agent

class AgentService:
    """
    Service applicatif :
    - Coordonne les repositories liés aux agents
    - Enrichit les entités avec leurs relations (affectations, régimes)
    - Délègue la validation métier au AgentValidatorService
    """

    def __init__(
        self,
        affectation_repo: AffectationRepositoryPort,
        agent_repo: AgentRepositoryPort,
        etat_jour_agent_repo: EtatJourAgentRepositoryPort,
        qualification_repo: QualificationRepositoryPort,
        regime_repo: RegimeRepositoryPort,
    ):
        self.affectation_repo = affectation_repo
        self.agent_repo = agent_repo
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.regime_repo = regime_repo
        self.qualification_repo = qualification_repo

    def activate(self, agent_id: int) -> bool:
        return self.agent_repo.set_active(agent_id, True)

    def count(self) -> int:
        return self.agent_repo.count()
    
    def create(
        self,
        *,
        nom: str,
        prenom: str,
        code_personnel: str = "",
        regime_id: Optional[int] = None,
        actif: bool = True,
    ) -> Agent:
        agent = Agent(
            id=0,
            nom=nom,
            prenom=prenom,
            code_personnel=code_personnel,
            regime_id=regime_id,
            actif=actif,
        )
        return self.agent_repo.create(agent)
    
    def deactivate(self, agent_id: int) -> bool:
        return self.agent_repo.set_active(agent_id, False)
    
    def get_by_id(self, agent_id: int) -> Agent | None:
        return self.agent_repo.get_by_id(agent_id)
    
    def list(self, *, limit: Optional[int] = None, offset: int = 0) -> List[Agent]:
        return self.agent_repo.list(limit=limit, offset=offset)
    
    def list_all(self) -> List[Agent]:
        return self.agent_repo.list_all()
    
    def update(self, agent_id: int, **changes: Any) -> Optional[Agent]:
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            return None

        # applique seulement ce qui est présent dans changes
        if "nom" in changes:
            agent.nom = changes["nom"]
        if "prenom" in changes:
            agent.prenom = changes["prenom"]
        if "code_personnel" in changes:
            agent.code_personnel = changes["code_personnel"]
        if "regime_id" in changes:
            agent.regime_id = changes["regime_id"]
        if "actif" in changes:
            agent.actif = changes["actif"]

        return self.agent_repo.update(agent)

    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_agent_complet(self, agent_id: int) -> Agent | None:
        """
        Récupère un agent enrichi avec son régime et ses affectations.
        """
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            return None

        return self._enrich_agent(agent)

    def list_agents_complets(
        self, *, limit: Optional[int] = None, offset: int = 0
    ) -> List[Agent]:
        """
        Retourne tous les agents enrichis avec leur régime, affectations et états journalier.
        """
        agents = self.agent_repo.list(limit=limit, offset=offset)

        return [self._enrich_agent(agent) for agent in agents]
    
    def _enrich_agent(self, agent: Agent) -> Agent:
        if agent.regime_id:
            agent.set_regime(self.regime_repo.get_by_id(agent.regime_id))

        agent.set_affectations(self.affectation_repo.list_for_agent(agent.id))
        agent.set_etat_jours(self.etat_jour_agent_repo.list_for_agent(agent.id))
        agent.set_qualifications(self.qualification_repo.list_for_agent(agent.id))
        return agent