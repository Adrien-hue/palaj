from datetime import date
from typing import List, Optional, Tuple

from core.utils.domain_alert import DomainAlert, Severity
from core.utils.logger import Logger

from db.repositories.agent_repo import AgentRepository 
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.tranche_repo import TrancheRepository

from core.domain.entities import Affectation, Agent, Tranche


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

    def can_assign(self, agent: Agent, tranche: Tranche, jour: date) -> Tuple[bool, List[DomainAlert]]:
        """
        Vérifie si un agent peut être affecté à une tranche pour un jour donné.
        Retourne (is_valid, alerts)
        """
        alerts: List[DomainAlert] = []
        
        # Paramètres invalides
        if agent is None or tranche is None:
            alerts.append(DomainAlert("Paramètres invalides transmis à can_assign()", Severity.ERROR, jour, "AffectationService"))
            return False, alerts

        etats = self.etat_jour_agent_repo.list_for_agent(agent.id)
        affectations = self.affectation_repo.list_for_agent(agent.id)

        # Déjà affecté ce jour 
        if any(a.jour == jour for a in affectations):
            alerts.append(DomainAlert(
                f"{agent.get_full_name()} déjà affecté le {jour}",
                Severity.ERROR,
                jour,
                "AffectationService"
            ))

        # Repos / congé / absence ?
        etat = next((e for e in etats if e.jour == jour), None)
        if etat and etat.type_jour in ("repos", "conge", "absence"):
            alerts.append(DomainAlert(
                f"{agent.get_full_name()} est en {etat.type_jour} le {jour}",
                Severity.ERROR,
                jour,
                "AffectationService"
            ))

        # Logging (si activé)
        for alert in alerts:
            self.logger.log_from_alert(alert)

        return (len(alerts) == 0, alerts)

    def create_affectation(
        self,
        agent: Agent,
        tranche: Tranche,
        jour: date,
        simulate: bool = True
    ) -> Tuple[bool, Optional[Affectation], List[DomainAlert]]:
        """
        Crée une affectation si elle est valide selon les règles métier.
        Retourne : (success, affectation, alerts)
        """
        alerts: List[DomainAlert] = []

        # Vérification de validité de base
        is_valid, can_alerts = self.can_assign(agent, tranche, jour)
        alerts.extend(can_alerts)

        if not is_valid:
            for alert in alerts:
                self.logger.log_from_alert(alert)
            return False, None, alerts

        affect = Affectation(agent.id, tranche.id, jour)

        # Tentative de création réelle
        if not simulate:
            try:
                self.affectation_repo.create(affect)
                self.logger.success(
                    f"✅ Affectation créée pour {agent.get_full_name()} sur {tranche.abbr} ({jour})"
                )
            except Exception as e:
                alert = DomainAlert(
                    f"Erreur lors de la création de l’affectation : {e}",
                    Severity.ERROR,
                    jour,
                    "AffectationService",
                )
                alerts.append(alert)
                self.logger.log_from_alert(alert)
                return False, None, alerts
        else:
            self.logger.info(
                f"[Simulation] Affectation possible pour {agent.get_full_name()} sur {tranche.abbr} ({jour})"
            )

        return True, affect, alerts

    # -------------
    # Vérifications
    # -------------
    def _check_agent(self, affectation: Affectation) -> List[DomainAlert]:
        """Vérifie que l'agent est valide et actif."""
        alerts = []
        if not affectation.agent_id:
            alerts.append(DomainAlert("Agent non spécifié.", Severity.ERROR, affectation.jour, "AffectationService"))
        elif affectation.get_agent(self.agent_repo) is None:
            alerts.append(DomainAlert(f"Agent introuvable (id={affectation.agent_id})", Severity.ERROR, affectation.jour, "AffectationService"))
        return alerts

    def _check_doublons(self, affectations: List[Affectation]) -> List[DomainAlert]:
        """Détecte les doublons d'affectation (même agent et même jour)."""
        alerts = []
        seen = set()
        for a in affectations:
            key = (a.agent_id, a.jour)
            if key in seen:
                alerts.append(DomainAlert(
                    f"Doublon détecté : agent {a.agent_id} affecté plusieurs fois le {a.jour}",
                    Severity.ERROR,
                    a.jour,
                    "AffectationService"
                ))
            seen.add(key)
        return alerts

    def _check_etat_jour(self, affectation: Affectation) -> List[DomainAlert]:
        """Vérifie que l'état du jour est cohérent avec la présence sur un poste."""
        alerts = []
        etats = self.etat_jour_agent_repo.list_for_agent(affectation.agent_id)
        etat = next((e for e in etats if e.jour == affectation.jour), None)
        
        if etat and etat.type_jour != "poste":
            alerts.append(DomainAlert(
                f"Affectation incohérente : agent {affectation.agent_id} affecté le {affectation.jour} alors que le jour est '{etat.type_jour}'",
                Severity.WARNING,
                affectation.jour,
                "AffectationService"
            ))
        return alerts
    
    def _check_tranche(self, affectation: Affectation) -> List[DomainAlert]:
        """Vérifie que la tranche est valide et active."""
        alerts = []
        if not affectation.tranche_id:
            alerts.append(DomainAlert("Tranche non spécifiée.", Severity.ERROR, affectation.jour, "AffectationService"))
        elif affectation.get_tranche(self.tranche_repo) is None:
            alerts.append(DomainAlert(f"Tranche introuvable (id={affectation.tranche_id})", Severity.ERROR, affectation.jour, "AffectationService"))
        return alerts

    # ------------
    # Validations
    # ------------
    def validate(self, affectation: Affectation) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide une seule affectation selon les règles de cohérence et RH.
        Retourne une liste d'alertes.
        """
        if affectation is None:
            return (False, [DomainAlert("Affectation vide ou invalide.", Severity.ERROR, source="AffectationService")])

        alerts: List[DomainAlert] = []

        alerts.extend(self._check_agent(affectation))
        alerts.extend(self._check_tranche(affectation))
        alerts.extend(self._check_etat_jour(affectation))

        return (len(alerts) == 0, alerts)

    def validate_by_id(self, affectation_id: str, verbose: bool = False) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide une affectation spécifique par son ID.
        Retourne (is_valid, alerts)
        """
        affectation = self.affectation_repo.get(affectation_id)
        
        if not affectation:
            return (False, [DomainAlert("Affectation vide ou invalide.", Severity.ERROR, source="AffectationService")])

        return self.validate(affectation)

    def validate_all(self) -> Tuple[bool, List[DomainAlert]]:
        """
        Exécute toutes les validations sur toutes les affectations du repo.
        Retourne (is_valid, alerts)
        """
        all_alerts = []

        list_affs = self.affectation_repo.list_all()

        all_alerts.extend(self._check_doublons(list_affs))

        for a in list_affs:
            _, alerts = self.validate(a)
            
            all_alerts.extend(alerts)

        is_valid = len(all_alerts) == 0

        if is_valid:
            self.logger.success(f"Toutes les affectations sont valides.")
        else:
            self.logger.warn(f"🚨 Problèmes détectés dans les affectations :")
            for a in all_alerts:
                self.logger.log_from_alert(a)

        return is_valid, all_alerts