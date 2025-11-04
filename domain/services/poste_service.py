from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from db.repositories.poste_repo import PosteRepository
from db.repositories.tranche_repo import TrancheRepository

class PosteService:
    """Service de validation structurelle des postes."""

    def __init__(self, poste_repo: PosteRepository, tranche_repo: TrancheRepository):
        self.poste_repo = poste_repo
        self.tranche_repo = tranche_repo

    def validate_all(self) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        seen_ids = set()

        for p in self.poste_repo.list_all():
            if p.id in seen_ids:
                alerts.append(DomainAlert(f"Doublon de poste ID {p.id}.", Severity.ERROR, source="PosteService"))
            seen_ids.add(p.id)

            for tid in p.tranche_ids:
                if not self.tranche_repo.get(tid):
                    alerts.append(DomainAlert(
                        f"Poste {p.nom} référence une tranche inexistante (ID {tid})",
                        Severity.ERROR, source="PosteService"
                    ))

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
