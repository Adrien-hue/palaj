from datetime import date
from typing import List, Tuple, Optional
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.entities import EtatJourAgent, Agent, TypeJour


class EtatJourAgentService:
    """
    Service applicatif :
    - Coordonne les repositories
    - Gère la création et la cohérence des états journaliers
    - Délègue la validation métier pure au ValidatorService
    """

    def __init__(self, etat_jour_agent_repo, affectation_repo, agent_repo):
        self.etat_jour_agent_repo = etat_jour_agent_repo
        self.affectation_repo = affectation_repo
        self.agent_repo = agent_repo

    # ---------------------------------------------------------
    # 🔹 Règles applicatives (création et cohérence)
    # ---------------------------------------------------------
    def can_add_state(self, agent: Agent, jour: date) -> Tuple[bool, List[DomainAlert]]:
        """Vérifie qu'on peut ajouter un état ce jour-là (pas de doublon)."""
        existing = self.etat_jour_agent_repo.list_for_agent(agent.id)
        if any(e.jour == jour for e in existing):
            return False, [
                DomainAlert(
                    f"L’agent {agent.get_full_name()} a déjà un état pour le {jour}.",
                    Severity.ERROR,
                    source="EtatJourAgentService"
                )
            ]
        return True, []

    def create_state(
        self,
        agent: Agent,
        jour: date,
        type_jour: TypeJour | str,
        description: str = "",
        simulate: bool = True,
    ) -> Tuple[bool, Optional[EtatJourAgent], List[DomainAlert]]:
        """Crée un état (avec simulation optionnelle)."""
        alerts: List[DomainAlert] = []

        # Normalisation du type
        if isinstance(type_jour, str):
            try:
                type_jour = TypeJour(type_jour)
            except ValueError:
                return False, None, [
                    DomainAlert(f"Type d’état invalide : '{type_jour}'", Severity.ERROR)
                ]

        # Vérifie possibilité d’ajout
        can_add, add_alerts = self.can_add_state(agent, jour)
        alerts.extend(add_alerts)
        if not can_add:
            return False, None, alerts

        etat = EtatJourAgent(agent.id, jour, type_jour, description)

        # Vérifie les incohérences
        incompat = self._check_incompatibilities(etat)
        alerts.extend(incompat)
        if any(a.is_error() for a in incompat):
            return False, None, alerts

        if not simulate:
            self.etat_jour_agent_repo.create(etat)

        return True, etat, alerts

    def ensure_poste_state(
        self,
        agent: Agent,
        jour: date,
        simulate: bool = True,
        auto_create: bool = True,
    ) -> Tuple[bool, Optional[EtatJourAgent], List[DomainAlert]]:
        """
        Garantit que si une affectation existe, un état 'POSTE' est présent.
        """
        alerts: List[DomainAlert] = []
        existing = self.etat_jour_agent_repo.list_for_agent(agent.id)
        etat_du_jour = next((e for e in existing if e.jour == jour), None)

        if etat_du_jour is None:
            if auto_create:
                return self.create_state(agent, jour, TypeJour.POSTE, simulate=simulate)
            else:
                alerts.append(DomainAlert(
                    f"Aucun état trouvé pour {agent.get_full_name()} le {jour}.",
                    Severity.WARNING,
                    source="EtatJourAgentService"
                ))
                return False, None, alerts

        if etat_du_jour.type_jour != TypeJour.POSTE:
            alerts.append(DomainAlert(
                f"Incohérence : {agent.get_full_name()} est '{etat_du_jour.type_jour.value}' le {jour}, "
                f"mais une affectation 'POSTE' existe.",
                Severity.WARNING,
                source="EtatJourAgentService"
            ))
            return False, etat_du_jour, alerts

        return True, etat_du_jour, alerts

    def _check_incompatibilities(self, etat: EtatJourAgent) -> List[DomainAlert]:
        """Détecte les conflits entre états et affectations."""
        alerts: List[DomainAlert] = []
        affectations = self.affectation_repo.list_for_agent(etat.agent_id)

        if etat.type_jour != TypeJour.POSTE:
            if any(a.jour == etat.jour for a in affectations):
                alerts.append(DomainAlert(
                    f"Incohérence : agent {etat.agent_id} a une affectation le {etat.jour} "
                    f"malgré un état '{etat.type_jour.value}'.",
                    Severity.WARNING,
                    source="EtatJourAgentService"
                ))

        return alerts
    
    # =========================================================
    # 🔹 Chargement
    # =========================================================
    def list_all(self) -> List[EtatJourAgent]:
        """Retourne tous les états journaliers."""
        return self.etat_jour_agent_repo.list_all()

    def list_for_agent(self, agent_id: int) -> List[EtatJourAgent]:
        """Retourne tous les états d’un agent."""
        return self.etat_jour_agent_repo.list_for_agent(agent_id)

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

        etat_jour_agent.set_agent(self.agent_repo.get(etat_jour_agent.agent_id))

        return etat_jour_agent

    def list_etats_jour_agent_complets(self) -> list[EtatJourAgent]:
        etats_jour_agent = self.etat_jour_agent_repo.list_all()
        
        for e in etats_jour_agent:
            e.set_agent(self.agent_repo.get(e.agent_id))

        return etats_jour_agent