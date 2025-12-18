# core/application/service/etat_jour_agent_service.py
from datetime import date
from typing import List

from core.application.ports import (
    AffectationRepositoryPort,
    AgentRepositoryPort,
    EtatJourAgentRepositoryPort,
)
from core.domain.entities import EtatJourAgent


class EtatJourAgentService:
    """
    Service applicatif :
    - Coordonne les repositories
    - Gère la création et la cohérence des états journaliers
    - Délègue la validation métier pure au ValidatorService
    """

    def __init__(
        self,
        affectation_repo: AffectationRepositoryPort,
        agent_repo: AgentRepositoryPort,
        etat_jour_agent_repo: EtatJourAgentRepositoryPort,
    ):
        self.affectation_repo = affectation_repo
        self.agent_repo = agent_repo
        self.etat_jour_agent_repo = etat_jour_agent_repo
    
    # =========================================================
    # 🔹 Chargement
    # =========================================================
    def list_all(self) -> List[EtatJourAgent]:
        """Retourne tous les états journaliers."""
        return self.etat_jour_agent_repo.list_all()
    
    def list_between_dates(
        self,
        date_start: date,
        date_end: date,
    ) -> List[EtatJourAgent]:
        """Retourne tous les états journaliers entre 2 dates."""
        return self.etat_jour_agent_repo.list_between_dates(date_start, date_end)

    def list_for_agent(self, agent_id: int) -> List[EtatJourAgent]:
        """Retourne tous les états d'un agent."""
        return self.etat_jour_agent_repo.list_for_agent(agent_id)

    def list_for_agent_between_dates(
        self,
        agent_id: int,
        date_start: date,
        date_end: date,
    ) -> List[EtatJourAgent]:
        """Retourne les états d'un agent entre 2 dates (bornes incluses)."""
        return self.etat_jour_agent_repo.list_for_agent_between_dates(
            agent_id, date_start, date_end
        )

    def get_for_agent_and_day(self, agent_id: int, jour: date) -> EtatJourAgent | None:
        """Retourne un état spécifique pour un agent à une date donnée."""
        return self.etat_jour_agent_repo.get_for_agent_and_day(agent_id, jour)
    
    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_etat_jour_agent_complet(self, agent_id: int, jour: date) -> EtatJourAgent | None:
        etat_jour_agent = self.etat_jour_agent_repo.get_for_agent_and_day(agent_id, jour)
        
        if not etat_jour_agent:
            return None

        etat_jour_agent.set_agent(self.agent_repo.get_by_id(etat_jour_agent.agent_id))

        return etat_jour_agent

    def list_etats_jour_agent_complets(self) -> list[EtatJourAgent]:
        etats_jour_agent = self.etat_jour_agent_repo.list_all()
        
        for e in etats_jour_agent:
            e.set_agent(self.agent_repo.get_by_id(e.agent_id))

        return etats_jour_agent