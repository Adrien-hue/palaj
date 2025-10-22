from dataclasses import dataclass
from datetime import date
from typing import List, Optional
from models.agent import Agent
from models.affectation import Affectation
from models.etat_jour_agent import EtatJourAgent

@dataclass
class PlanningContext:
    """
    Représente le contexte de planification pour un agent donné.
    Permet de vérifier ou simuler des règles RH.
    """
    agent: Agent
    existing_affectations: List[Affectation]
    etats_jour: List[EtatJourAgent]
    simulated_affectation: Optional[Affectation] = None
    date_reference: Optional[date] = None

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