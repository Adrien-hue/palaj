# core/application/service/agent_service.py
from typing import List
from core.domain.entities.agent import Agent


class AgentService:
    """
    Service applicatif :
    - Coordonne les repositories liés aux agents
    - Enrichit les entités avec leurs relations (affectations, régimes)
    - Délègue la validation métier au AgentValidatorService
    """

    def __init__(self, agent_repo, affectation_repo, etat_jour_agent_repo, regime_repo, qualification_repo):
        self.agent_repo = agent_repo
        self.affectation_repo = affectation_repo
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.regime_repo = regime_repo
        self.qualification_repo = qualification_repo

    def list_all(self) -> List[Agent]:
        return self.agent_repo.list_all()
    
    def get(self, agent_id: int) -> Agent | None:
        return self.agent_repo.get(agent_id)

    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_agent_complet(self, agent_id: int) -> Agent | None:
        """
        Récupère un agent enrichi avec son régime et ses affectations.
        """
        agent = self.agent_repo.get(agent_id)
        if not agent:
            return None

        # Charger le régime
        if agent.regime_id:
            agent.set_regime(self.regime_repo.get(agent.regime_id))

        # Charger les affectations
        agent.set_affectations(self.affectation_repo.list_for_agent(agent.id))

        agent.set_etat_jours(self.etat_jour_agent_repo.list_for_agent(agent.id))

        agent.set_qualifications(self.qualification_repo.list_for_agent(agent.id))

        return agent

    def list_agents_complets(self) -> List[Agent]:
        """
        Retourne tous les agents enrichis avec leur régime, affectations et états journalier.
        """
        agents = self.agent_repo.list_all()
        for a in agents:
            if a.regime_id:
                a.set_regime(self.regime_repo.get(a.regime_id))

            a.set_affectations(self.affectation_repo.list_for_agent(a.id))

            a.set_etat_jours(self.etat_jour_agent_repo.list_for_agent(a.id))

            a.set_qualifications(self.qualification_repo.list_for_agent(a.id))

        return agents