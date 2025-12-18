# core/application/service/affectation_service.py
from datetime import date
from typing import List, Optional

from core.application.ports import (
    AffectationRepositoryPort,
    AgentRepositoryPort,
    TrancheRepositoryPort
)
from core.domain.entities import Affectation

class AffectationService:
    """
    Service applicatif :
    - Coordonne les repositories Affectation / Agent / Tranche
    - Enrichit les entités avec leurs dépendances
    - Délègue la validation métier au AffectationValidatorService
    """

    def __init__(
        self,
        affectation_repo: AffectationRepositoryPort,
        agent_repo: AgentRepositoryPort,
        tranche_repo: TrancheRepositoryPort,
    ):
        self.affectation_repo = affectation_repo
        self.agent_repo = agent_repo
        self.tranche_repo = tranche_repo

    # =========================================================
    # 🔹 Chargement
    # =========================================================
    def list_affectations(self) -> List[Affectation]:
        """Retourne toutes les affectations (niveau entité)."""
        return self.affectation_repo.list_all()

    def list_for_agent(self, agent_id: int) -> List[Affectation]:
        """Retourne les affectations d'un agent."""
        return self.affectation_repo.list_for_agent(agent_id)

    def list_for_day(self, jour) -> List[Affectation]:
        """Retourne toutes les affectations d'un jour donné."""
        return self.affectation_repo.list_for_day(jour)
    
    def list_for_poste(self, poste_id: int, start: Optional[date] = None, end: Optional[date] = None) -> List[Affectation]:
        """Retourne toutes les affectations d'un poste donné."""
        return self.affectation_repo.list_for_poste(poste_id, start, end)
    
    # =========================================================
    # 🔹 Chargement complet
    # =========================================================
    def get_affectation_complet(self, agent_id: int, jour: date) -> Affectation | None:
        """
        Charge les entités liées (Agent, Tranche) pour une affectation donnée.
        """
        affectation = self.affectation_repo.get_for_agent_and_day(agent_id, jour)

        if not affectation:
            return None

        affectation.set_agent(self.agent_repo.get_by_id(affectation.agent_id))
        affectation.set_tranche(self.tranche_repo.get_by_id(affectation.tranche_id))
        return affectation

    def list_affectations_completes(self) -> List[Affectation]:
        """
        Retourne toutes les affectations enrichies avec leurs dépendances.
        """
        affectations = self.list_affectations()

        for a in affectations:
            a.set_agent(self.agent_repo.get_by_id(a.agent_id))
            a.set_tranche(self.tranche_repo.get_by_id(a.tranche_id))

        return affectations