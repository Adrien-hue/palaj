from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository

from models.agent import Agent
from models.affectation import Affectation
from models.etat_jour_agent import EtatJourAgent


@dataclass
class PlanningContext:
    """Représente le contexte de planification pour un agent donné."""

    agent: Agent
    existing_affectations: List[Affectation]
    etats_jour: List[EtatJourAgent]
    simulated_affectation: Optional[Affectation] = None
    date_reference: Optional[date] = None

    # ------------------------------------------------------------
    @classmethod
    def from_repositories(
        cls,
        agent: Agent,
        jour: date,
        affectation_repo: AffectationRepository,
        etat_repo: EtatJourAgentRepository,
        simulated_affectation: Optional[Affectation] = None,
    ) -> "PlanningContext":
        """Fabrique un contexte basé sur l'état courant des dépôts."""

        affectations = sorted(
            affectation_repo.list_for_agent(agent.id),
            key=lambda a: a.jour,
        )
        etats = sorted(
            etat_repo.list_for_agent(agent.id),
            key=lambda e: e.jour,
        )

        return cls(
            agent=agent,
            existing_affectations=affectations,
            etats_jour=etats,
            simulated_affectation=simulated_affectation,
            date_reference=jour,
        )

    # ------------------------------------------------------------
    def get_all_affectations(self) -> List[Affectation]:
        """Retourne toutes les affectations (existantes + simulée si présente)."""
        if self.simulated_affectation:
            return self.existing_affectations + [self.simulated_affectation]
        return self.existing_affectations

    def get_last_affectation_before(self, jour: date) -> Optional[Affectation]:
        """Retourne la dernière affectation avant une date donnée."""
        before = [a for a in self.get_all_affectations() if a.jour < jour]
        return max(before, key=lambda a: a.jour, default=None)

    def get_next_affectation_after(self, jour: date) -> Optional[Affectation]:
        """Retourne la première affectation après une date donnée."""
        after = [a for a in self.get_all_affectations() if a.jour > jour]
        return min(after, key=lambda a: a.jour, default=None)
