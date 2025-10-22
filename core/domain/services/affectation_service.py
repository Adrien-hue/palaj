from datetime import date
from typing import List, Optional, Tuple

from core.utils.logger import Logger

from db.repositories.agent_repo import AgentRepository 
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.tranche_repo import TrancheRepository

from models.affectation import Affectation
from models.agent import Agent
from models.tranche import Tranche
from models.etat_jour_agent import EtatJourAgent


class AffectationService:
    """
    Service métier responsable de la création, validation et gestion des affectations.
    """

    def __init__(
            self,
            agent_repo: AgentRepository,
            affectation_repo: AffectationRepository,
            etat_jour_agent_repo: EtatJourAgentRepository,
            tranche_repo: TrancheRepository,
            verbose: bool = False
        ):
        self.agent_repo = agent_repo
        self.affectation_repo = affectation_repo
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.tranche_repo = tranche_repo

        self.logger = Logger(verbose=verbose)

    # --- Vérifications métier ---
    def can_assign(self, agent: Agent, tranche: Tranche, jour: date) -> bool:
        """
        Vérifie si un agent peut être affecté à une tranche pour un jour donné.
        """

        if agent is None or tranche is None:
            self.logger.error("Paramètres invalides transmis à can_assign().")
            return False
        
        etats = self.etat_jour_agent_repo.list_for_agent(agent.id)
        affectations = self.affectation_repo.list_for_agent(agent.id)

        # Déjà affecté ce jour 
        if any(a.jour == jour for a in affectations):
            self.logger.error(f"Impossible d'affecter {agent.get_full_name()} sur {tranche.abbr} le {jour} (déjà affecté)")
            return False

        # Repos / congé / absence ?
        etat = next((e for e in etats if e.jour == jour), None)
        if etat and etat.type_jour in ("repos", "conge", "absence"):
            self.logger.error(f"Impossible d'affecter {agent.get_full_name()} sur {tranche.abbr} le {jour} ({etat.type_jour})")
            return False

        return True

    # --- Création ---
    def create_affectation(self, agent: Agent, tranche: Tranche, jour: date, simulate: bool = True) -> Optional[Affectation]:
        """
        Crée une affectation si elle est valide selon les règles métier.
        """
        if not self.can_assign(agent, tranche, jour):
            self.logger.warn(f"Impossible d'affecter {agent.get_full_name()} sur {tranche.abbr} le {jour} (règle RH)")
            return None

        affect = Affectation(agent.id, tranche.id, jour)
        if not simulate:
            try:
                self.affectation_repo.create(affect)
                self.logger.success(
                    f"✅ Affectation créée pour {agent.get_full_name()} sur {tranche.abbr} ({jour})"
                )
            except Exception as e:
                self.logger.error(f"Erreur lors de la création de l'affectation : {e}")
                return None
        else:
            self.logger.info(
                f"[Simulation] Affectation possible pour {agent.get_full_name()} sur {tranche.abbr} ({jour})"
            )

        return affect

    def _check_agent(self, affectation: Affectation) -> List[str]:
        """Vérifie que l'agent est valide et actif."""
        alerts = []
        if not affectation.agent_id:
            alerts.append("❌ Agent non spécifié.")
        elif affectation.get_agent(self.agent_repo) is None:
            alerts.append("❌ Agent introuvable.")
        return alerts

    def _check_doublons(self, affectations: List[Affectation]) -> List[str]:
        """Détecte les doublons d'affectation (même agent et même jour)."""
        alerts = []
        seen = set()

        for a in affectations:
            key = (a.agent_id, a.jour)
            if key in seen:
                alerts.append(
                    f"❌ Doublon détecté : agent {a.agent_id} affecté plusieurs fois le {a.jour}"
                )
            seen.add(key)

        return alerts

    def _check_etat_jour(self, affectation: Affectation) -> List[str]:
        """Vérifie que l'état du jour est cohérent avec la présence sur un poste."""
        alerts = []

        etats = self.etat_jour_agent_repo.list_for_agent(affectation.agent_id)
        etat = next((e for e in etats if e.jour == affectation.jour), None)
        
        if etat and etat.type_jour != "poste":
            alerts.append(
                f"⚠️ Affectation incohérente : agent {affectation.agent_id} affecté "
                f"le {affectation.jour} alors que le jour est marqué '{etat.type_jour}'"
            )
        
        return alerts
    
    def _check_tranche(self, affectation: Affectation) -> List[str]:
        """Vérifie que la tranche est valide et active."""
        alerts = []
        if not affectation.tranche_id:
            alerts.append("❌ Tranche non spécifiée.")
        elif affectation.get_tranche(self.tranche_repo) is None:
            alerts.append("❌ Tranche introuvable.")
        return alerts

    # ------------
    # Validations
    # ------------
    def validate(self, affectation: Affectation) -> Tuple[bool, List[str]]:
        """
        Valide une seule affectation selon les règles de cohérence et RH.
        Retourne une liste d'alertes.
        """
        if affectation is None:
            return (False, ["❌ Affectation vide ou invalide."])

        alerts: List[str] = []

        alerts.extend(self._check_agent(affectation))
        alerts.extend(self._check_tranche(affectation))
        alerts.extend(self._check_etat_jour(affectation))

        return (len(alerts) == 0, alerts)

    def validate_by_id(self, affectation_id: str, verbose: bool = False) -> Tuple[bool, List[str]]:
        """
        Valide une affectation spécifique par son ID.
        Retourne (is_valid, alerts)
        """
        affectation = self.affectation_repo.get(affectation_id)
        if not affectation:
            msg = f"Affectation introuvable (ID={affectation_id})"
            self.logger.error(msg)
            return False, [msg]

        return self.validate(affectation)

    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        Exécute toutes les validations sur toutes les affectations du repo.
        Retourne (is_valid, alerts)
        """
        alerts = []

        list_affs = self.affectation_repo.list_all()

        alerts.extend(self._check_doublons(list_affs))

        for a in list_affs:
            _, alerts = self.validate(a)
            
            alerts.extend(alerts)

        is_valid = len(alerts) == 0

        if len(alerts) == 0:
            self.logger.success(f"Toutes les affectations sont valides.")
        else:
            self.logger.warn(f"🚨 Problèmes détectés dans les affectations :")
            for a in alerts:
                self.logger.warn("  - " + a)

        return is_valid, alerts