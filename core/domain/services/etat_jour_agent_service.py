from datetime import date
from typing import Optional, List

from core.utils.logger import Logger

from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository

from models.agent import Agent
from models.etat_jour_agent import EtatJourAgent

class EtatJourAgentService:
    """
    Gère les états journaliers d'un agent (repos, congé, absence, zcot, etc.)
    """

    def __init__(self, etat_repo: EtatJourAgentRepository, verbose: bool = False):
        self.etat_repo = etat_repo

        self.logger = Logger(verbose=verbose)

    def can_add_state(self, agent: Agent, jour: date) -> bool:
        """Vérifie si un état peut être ajouté pour un jour donné (pas de doublon ni conflit)."""
        existing = self.etat_repo.list_for_agent(agent.id)
        return all(e.jour != jour for e in existing)

    def create_state(self, agent: Agent, jour: date, type_jour: str, description: str = "", simulate: bool = True) -> Optional[EtatJourAgent]:
        """Crée un nouvel état (repos, congé, absence, etc.)"""
        if not self.can_add_state(agent, jour):
            self.logger.error(f"L'agent {agent.get_full_name()} a déjà un état pour le {jour}")
            return None

        # Convert type_jour string to TYPE_JOUR type if necessary
        from models.etat_jour_agent import TYPE_JOUR
        type_jour_enum: TYPE_JOUR = type_jour  # type: ignore
        etat = EtatJourAgent(agent.id, jour, type_jour_enum, description)
        if not simulate:
            self.etat_repo.create(etat)
        return etat

    def ensure_poste_state(
        self,
        agent: Agent,
        jour: date,
        simulate: bool = True,
        auto_create: bool = True,
    ) -> Optional[EtatJourAgent]:
        """
        Vérifie que l'état du jour pour un agent est bien 'poste'.
        - Si aucun état n'existe et auto_create=True, il est créé automatiquement.
        - Si un autre type existe (ex: repos/congé), renvoie None et un avertissement.
        """
        existing = self.etat_repo.list_for_agent(agent.id)
        etat_du_jour = next((e for e in existing if e.jour == jour), None)

        if etat_du_jour is None:
            if auto_create:
                self.logger.info(f"Création automatique de l'état 'poste' pour {agent.get_full_name()} le {jour}")
                return self.create_state(agent, jour, "poste", simulate=simulate)
            else:
                self.logger.info(f"Aucun état trouvé pour {agent.get_full_name()} le {jour}")
                return None

        if etat_du_jour.type_jour != "poste":
            self.logger.warn(
                f"Incohérence : {agent.get_full_name()} est marqué comme '{etat_du_jour.type_jour}' le {jour}, "
                f"mais une affectation 'poste' est présente."
            )
            return None

        # Déjà correct
        return etat_du_jour