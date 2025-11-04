from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from db.repositories.regime_repo import RegimeRepository

class RegimeService:
    """Vérifie la validité des régimes."""

    def __init__(self, regime_repo: RegimeRepository):
        self.regime_repo = regime_repo

    def validate_all(self) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        seen_ids = set()

        for r in self.regime_repo.list_all():
            if r.id in seen_ids:
                alerts.append(DomainAlert(
                    f"Doublon de régime ID {r.id}.", Severity.ERROR, source="RegimeService"
                ))
            seen_ids.add(r.id)

            if r.duree_moyenne_journee_service_min < 0:
                alerts.append(DomainAlert(
                    f"Durée moyenne négative pour le régime {r.nom}.",
                    Severity.ERROR, source="RegimeService"
                ))

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
