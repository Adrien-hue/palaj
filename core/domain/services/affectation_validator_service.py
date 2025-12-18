from datetime import date, timedelta
from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.entities.affectation import Affectation


class AffectationValidatorService:
    """
    Service de domaine : validation métier pure des affectations.
    Ne dépend d'aucune base de données ni repository.
    """

    # =========================================================
    # 🔹 Vérifications internes
    # =========================================================
    def _check_doublons(self, affectations: List[Affectation]) -> List[DomainAlert]:
        """Vérifie qu'un agent n'a pas deux affectations le même jour."""
        alerts: List[DomainAlert] = []
        seen_pairs = set()

        for a in affectations:
            key = (a.agent_id, a.jour)
            if key in seen_pairs:
                alerts.append(DomainAlert(
                    f"Doublon d'affectation : agent {a.agent_id} a plusieurs affectations le {a.jour}.",
                    Severity.ERROR,
                    source="AffectationValidatorService"
                ))
            seen_pairs.add(key)
        return alerts

    def _check_coherence(self, a: Affectation) -> List[DomainAlert]:
        """Vérifie la cohérence d'une affectation individuelle."""
        alerts: List[DomainAlert] = []

        # Champs obligatoires
        if a.agent_id is None:
            alerts.append(DomainAlert(
                "Affectation sans agent associé.",
                Severity.ERROR,
                source="AffectationValidatorService"
            ))

        if a.tranche_id is None:
            alerts.append(DomainAlert(
                f"Affectation du {a.jour} sans tranche associée.",
                Severity.ERROR,
                source="AffectationValidatorService"
            ))

        if not a.jour:
            alerts.append(DomainAlert(
                "Affectation sans date définie.",
                Severity.ERROR,
                source="AffectationValidatorService"
            ))

        # Cohérence temporelle
        if isinstance(a.jour, date):
            today = date.today()
            if a.jour < date(2000, 1, 1):
                alerts.append(DomainAlert(
                    f"Affectation avec date incohérente ({a.jour}).",
                    Severity.WARNING,
                    source="AffectationValidatorService"
                ))
            if a.jour > today + timedelta(days=365 * 2):
                alerts.append(DomainAlert(
                    f"Affectation projetée trop loin dans le futur ({a.jour}).",
                    Severity.WARNING,
                    source="AffectationValidatorService"
                ))

        return alerts

    # =========================================================
    # 🔹 Validation unitaire
    # =========================================================
    def validate(self, affectation: Affectation) -> Tuple[bool, List[DomainAlert]]:
        alerts = self._check_coherence(affectation)
        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts

    # =========================================================
    # 🔹 Validation globale
    # =========================================================
    def validate_all(self, affectations: List[Affectation]) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_doublons(affectations))

        for a in affectations:
            _, local_alerts = self.validate(a)
            alerts.extend(local_alerts)

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts
