from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from db.repositories.agent_repo import AgentRepository

class AgentService:
    """Service métier de validation des agents."""

    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    def validate(self, agent) -> Tuple[bool, List[DomainAlert]]:
        alerts = []
        if not agent.nom or not agent.prenom:
            alerts.append(DomainAlert(
                f"Agent {agent.id} sans nom ou prénom défini.",
                Severity.WARNING, source="AgentService"
            ))
        if agent.id is None:
            alerts.append(DomainAlert(
                f"Agent sans identifiant unique.",
                Severity.ERROR, source="AgentService"
            ))
        return (len([a for a in alerts if a.is_error()]) == 0, alerts)

    def validate_all(self) -> Tuple[bool, List[DomainAlert]]:
        all_agents = self.agent_repo.list_all()
        alerts: List[DomainAlert] = []

        seen_ids = set()
        for a in all_agents:
            if a.id in seen_ids:
                alerts.append(DomainAlert(
                    f"Doublon d'agent ID {a.id}.",
                    Severity.ERROR, source="AgentService"
                ))
            seen_ids.add(a.id)
            _, local_alerts = self.validate(a)
            alerts.extend(local_alerts)

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts