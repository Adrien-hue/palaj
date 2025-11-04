from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.agent_repo import AgentRepository
from db.repositories.poste_repo import PosteRepository

class QualificationService:
    """Vérifie la cohérence des qualifications agent ↔ poste."""

    def __init__(self, qualification_repo: QualificationRepository, agent_repo: AgentRepository, poste_repo: PosteRepository):
        self.qualification_repo = qualification_repo
        self.agent_repo = agent_repo
        self.poste_repo = poste_repo

    def validate_all(self) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        seen = set()

        for q in self.qualification_repo.list_all():
            key = (q.agent_id, q.poste_id)
            if key in seen:
                alerts.append(DomainAlert(
                    f"Doublon de qualification (agent={q.agent_id}, poste={q.poste_id}).",
                    Severity.WARNING, source="QualificationService"
                ))
            seen.add(key)

            if not self.agent_repo.get(q.agent_id):
                alerts.append(DomainAlert(
                    f"Qualification référence agent inexistant ({q.agent_id}).",
                    Severity.ERROR, source="QualificationService"
                ))
            if not self.poste_repo.get(q.poste_id):
                alerts.append(DomainAlert(
                    f"Qualification référence poste inexistant ({q.poste_id}).",
                    Severity.ERROR, source="QualificationService"
                ))

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
