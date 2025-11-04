from datetime import date
from typing import Optional, List, Tuple

from core.utils.domain_alert import DomainAlert, Severity
from core.utils.logger import Logger

from db.repositories.affectation_repo import AffectationRepository
from db.repositories.agent_repo import AgentRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository

from core.domain.entities import Agent, EtatJourAgent, TypeJour

class EtatJourAgentService:
    """
    Gère les états journaliers d'un agent (repos, congé, absence, zcot, etc.)
    """

    def __init__(
        self,
        etat_jour_agent_repo: EtatJourAgentRepository,
        affectation_repo: AffectationRepository,
        agent_repo: AgentRepository,
        verbose: bool = False,
    ):
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.affectation_repo = affectation_repo
        self.agent_repo = agent_repo
        self.logger = Logger(verbose=verbose)

    def can_add_state(self, agent: Agent, jour: date) -> Tuple[bool, List[DomainAlert]]:
        """Vérifie si un état peut être ajouté ce jour-là (pas de doublon)."""
        alerts: List[DomainAlert] = []
        existing = self.etat_jour_agent_repo.list_for_agent(agent.id)

        if any(e.jour == jour for e in existing):
            alerts.append(
                DomainAlert(
                    f"L'agent {agent.get_full_name()} a déjà un état pour le {jour}.",
                    Severity.ERROR,
                    jour,
                    "EtatJourAgentService",
                )
            )

        for alert in alerts:
            self.logger.log_from_alert(alert)

        return len(alerts) == 0, alerts
    
    def create_state(
        self,
        agent: Agent,
        jour: date,
        type_jour: TypeJour | str,
        description: str = "",
        simulate: bool = True,
    ) -> Tuple[bool, Optional[EtatJourAgent], List[DomainAlert]]:
        """
        Crée un nouvel état pour un agent si les règles le permettent.
        Retourne : (success, etat, alerts)
        """
        alerts: List[DomainAlert] = []

        # Conversion automatique str -> Enum
        if isinstance(type_jour, str):
            try:
                type_jour = TypeJour(type_jour)
            except ValueError:
                alert = DomainAlert(
                    f"Type d'état invalide : '{type_jour}'",
                    Severity.ERROR,
                    jour,
                    "EtatJourAgentService",
                )
                alerts.append(alert)
                self.logger.log_from_alert(alert)
                return False, None, alerts

        can_add, add_alerts = self.can_add_state(agent, jour)
        alerts.extend(add_alerts)
        if not can_add:
            return False, None, alerts

        etat = EtatJourAgent(agent.id, jour, type_jour, description)

        # Vérifications métier supplémentaires
        incompat = self._check_incompatibilities(etat)
        alerts.extend(incompat)

        for alert in incompat:
            self.logger.log_from_alert(alert)

        if any(a.severity is Severity.ERROR for a in incompat):
            return False, None, alerts

        if not simulate:
            self.etat_jour_agent_repo.create(etat)
            self.logger.success(f"✅ État '{type_jour.value}' créé pour {agent.get_full_name()} le {jour}")
        else:
            self.logger.info(f"[Simulation] État '{type_jour.value}' possible pour {agent.get_full_name()} le {jour}")

        return True, etat, alerts

    def ensure_poste_state(
        self,
        agent: Agent,
        jour: date,
        simulate: bool = True,
        auto_create: bool = True,
    ) -> Tuple[bool, Optional[EtatJourAgent], List[DomainAlert]]:
        """
        Garantit que l'état du jour est 'poste' si une affectation existe.
        Retourne : (success, etat, alerts)
        """
        alerts: List[DomainAlert] = []
        existing = self.etat_jour_agent_repo.list_for_agent(agent.id)
        etat_du_jour = next((e for e in existing if e.jour == jour), None)

        # Aucun état existant
        if etat_du_jour is None:
            if auto_create:
                self.logger.info(f"Création automatique de l'état 'poste' pour {agent.get_full_name()} le {jour}")
                success, etat, new_alerts = self.create_state(
                    agent, jour, TypeJour.POSTE, simulate=simulate
                )
                alerts.extend(new_alerts)
                return success, etat, alerts
            else:
                alert = DomainAlert(
                    f"Aucun état trouvé pour {agent.get_full_name()} le {jour}.",
                    Severity.WARNING,
                    jour,
                    "EtatJourAgentService",
                )
                alerts.append(alert)
                self.logger.log_from_alert(alert)
                return False, None, alerts

        # Mauvais type existant
        if etat_du_jour.type_jour is not TypeJour.POSTE:
            alert = DomainAlert(
                f"Incohérence : {agent.get_full_name()} est marqué '{etat_du_jour.type_jour.value}' le {jour}, "
                f"mais une affectation 'poste' existe.",
                Severity.WARNING,
                jour,
                "EtatJourAgentService",
            )
            alerts.append(alert)
            self.logger.log_from_alert(alert)
            return False, None, alerts

        # Tout est cohérent
        return True, etat_du_jour, alerts
    
    # -------------
    # Vérifications
    # -------------
    def _check_agent(self, etat: EtatJourAgent) -> List[DomainAlert]:
        alerts = []
        agent = self.agent_repo.get(etat.agent_id)
        if not agent:
            alerts.append(DomainAlert(f"Agent inexistant (id={etat.agent_id})", Severity.ERROR, etat.jour, "EtatJourAgentService"))
        return alerts
    
    def _check_doublons(self, etats: List[EtatJourAgent]) -> List[DomainAlert]:
        alerts = []
        seen = set()
        for e in etats:
            key = (e.agent_id, e.jour)
            if key in seen:
                alerts.append(DomainAlert(f"Doublon d'état pour agent {e.agent_id} le {e.jour}", Severity.ERROR, e.jour, "EtatJourAgentService"))
            seen.add(key)
        return alerts
    
    def _check_incompatibilities(self, etat: EtatJourAgent) -> List[DomainAlert]:
        """
        Vérifie les incohérences logiques simples (ex : doublons, conflit de type).
        """
        alerts: List[DomainAlert] = []

        existing = self.etat_jour_agent_repo.list_for_agent(etat.agent_id)
        same_day = [e for e in existing if e.jour == etat.jour and e.id != etat.id]

        if same_day:
            alerts.append(
                DomainAlert(
                    f"Conflit détecté : plusieurs états le {etat.jour} pour l'agent {etat.agent_id}.",
                    Severity.ERROR,
                    etat.jour,
                    "EtatJourAgentService",
                )
            )

        # Exemples de conflits métier simples
        if etat.type_jour is not TypeJour.POSTE:
            affectations = self.affectation_repo.list_for_agent(etat.agent_id)
            if any(a.jour == etat.jour for a in affectations):
                alerts.append(
                    DomainAlert(
                        f"Incohérence : agent {etat.agent_id} a une affectation le {etat.jour} "
                        f"malgré un état '{etat.type_jour.value}'.",
                        Severity.WARNING,
                        etat.jour,
                        "EtatJourAgentService",
                    )
                )

        return alerts

    def _check_type(self, etat: EtatJourAgent) -> List[DomainAlert]:
        alerts = []
        try:
            # Essaye de normaliser vers Enum
            if not isinstance(etat.type_jour, TypeJour):
                TypeJour(etat.type_jour)
        except Exception:
            alerts.append(
                DomainAlert(
                    f"Type d'état inconnu : '{etat.type_jour}'",
                    Severity.ERROR,
                    etat.jour,
                    "EtatJourAgentService",
                )
            )
        return alerts

    # ------------
    # Validations
    # ------------
    def validate(self, etat: EtatJourAgent) -> Tuple[bool, List[DomainAlert]]:
        if etat is None:
            alert = DomainAlert("État de jour vide ou invalide.", Severity.ERROR, source="EtatJourAgentService")
            self.logger.log_from_alert(alert)
            return False, [alert]

        alerts: List[DomainAlert] = []
        alerts.extend(self._check_agent(etat))
        alerts.extend(self._check_type(etat))
        alerts.extend(self._check_incompatibilities(etat))

        for alert in alerts:
            self.logger.log_from_alert(alert)

        is_valid = not any(a.is_error() for a in alerts)
        return is_valid, alerts
    
    def validate_by_id(self, etat_id: str) -> Tuple[bool, List[DomainAlert]]:
        etat = self.etat_jour_agent_repo.get(etat_id)
        if not etat:
            alert = DomainAlert(f"État introuvable (ID={etat_id})", Severity.ERROR, source="EtatJourAgentService")
            self.logger.log_from_alert(alert)
            return False, [alert]
        return self.validate(etat)

    def validate_for_agent(self, agent: Agent) -> Tuple[bool, List[DomainAlert]]:
        etats = self.etat_jour_agent_repo.list_for_agent(agent.id)
        alerts: List[DomainAlert] = []

        # Vérifie les doublons sur l’ensemble du planning
        alerts.extend(self._check_doublons(etats))

        # Vérifie chaque jour
        for e in etats:
            _, e_alerts = self.validate(e)
            alerts.extend(e_alerts)

        for alert in alerts:
            self.logger.log_from_alert(alert)

        is_valid = not any(a.is_error() for a in alerts)
        return is_valid, alerts

    def validate_all(self) -> Tuple[bool, List[DomainAlert]]:
        etats = self.etat_jour_agent_repo.list_all()
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_doublons(etats))

        for e in etats:
            _, e_alerts = self.validate(e)
            alerts.extend(e_alerts)

        for alert in alerts:
            self.logger.log_from_alert(alert)

        is_valid = not any(a.is_error() for a in alerts)
        if is_valid:
            self.logger.success("✅ Tous les états journaliers sont valides.")
        else:
            self.logger.warn(f"🚨 {len(alerts)} anomalies détectées dans les états journaliers.")

        return is_valid, alerts