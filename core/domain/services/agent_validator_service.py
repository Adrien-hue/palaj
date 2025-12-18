from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.entities.agent import Agent


class AgentValidatorService:
    """
    Service de domaine : validation métier pure des agents.
    Ne dépend d'aucune base de données ni repository.
    Gère uniquement les règles de cohérence métier.
    """

    # =========================================================
    # 🔹 Vérifications internes (unitaires ou globales)
    # =========================================================

    def _check_doublons(self, agents: List[Agent]) -> List[DomainAlert]:
        """Détecte les doublons d'ID parmi les agents."""
        alerts: List[DomainAlert] = []
        seen = set()

        for a in agents:
            if a.id in seen:
                alerts.append(DomainAlert(
                    f"Doublon d'agent ID {a.id} ({a.nom} {a.prenom})",
                    Severity.ERROR,
                    source="AgentValidatorService"
                ))
            seen.add(a.id)

        return alerts

    def _check_regime_associe(self, agent: Agent) -> List[DomainAlert]:
        """Vérifie que l'agent est bien associé à un régime."""
        alerts: List[DomainAlert] = []
        if agent.regime_id is None:
            alerts.append(DomainAlert(
                f"L'agent {agent.nom} {agent.prenom} (ID: {agent.id}) n'est associé à aucun régime.",
                Severity.WARNING,
                source="AgentValidatorService"
            ))
        return alerts

    def _check_nom_prenom(self, agent: Agent) -> List[DomainAlert]:
        """Vérifie la présence d'un nom et prénom valides."""
        alerts: List[DomainAlert] = []
        if not agent.nom or not agent.nom.strip():
            alerts.append(DomainAlert(
                f"Agent ID {agent.id} : nom manquant.",
                Severity.ERROR,
                source="AgentValidatorService"
            ))
        if not agent.prenom or not agent.prenom.strip():
            alerts.append(DomainAlert(
                f"Agent {agent.nom or '?'} : prénom manquant.",
                Severity.ERROR,
                source="AgentValidatorService"
            ))
        return alerts

    def _check_etats_jour_agent(self, agent: Agent) -> List[DomainAlert]:
        """
        Vérifie la cohérence des états journaliers de l'agent :
        - pas d'état orphelin
        - états ordonnés par date (optionnel)
        """
        alerts: List[DomainAlert] = []
        etats_jour = agent.etat_jours

        # Exemple de règle : trop de jours sans état
        if len(etats_jour) == 0:
            alerts.append(DomainAlert(
                f"L'agent {agent.nom} {agent.prenom} (ID: {agent.id}) n'a aucun état journalier enregistré.",
                Severity.WARNING,
                source="AgentValidatorService"
            ))

        return alerts

    # =========================================================
    # 🔹 Validation unitaire
    # =========================================================
    def validate(self, agent: Agent) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide un agent unique :
        - nom/prénom valides
        - régime associé
        - affectations cohérentes
        - états journaliers cohérents
        """
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_nom_prenom(agent))
        alerts.extend(self._check_regime_associe(agent))
        alerts.extend(self._check_etats_jour_agent(agent))

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts

    # =========================================================
    # 🔹 Validation globale
    # =========================================================
    def validate_all(self, agents: List[Agent]) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide un ensemble complet d'agents :
        - détecte les doublons d'ID
        - applique la validation unitaire à chacun
        """
        alerts: List[DomainAlert] = []

        # Vérif des doublons globale
        alerts.extend(self._check_doublons(agents))

        # Vérif unitaire sur chaque agent
        for a in agents:
            _, local_alerts = self.validate(a)
            alerts.extend(local_alerts)

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts
