from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.entities.etat_jour_agent import EtatJourAgent, TypeJour


class EtatJourAgentValidatorService:
    """
    Service de domaine :
    Validation métier pure des états journaliers des agents.
    Ne dépend pas de la base de données.
    """

    # ---------------------------------------------------------
    # 🔹 Vérifications internes
    # ---------------------------------------------------------
    def _check_doublons(self, etats: List[EtatJourAgent]) -> List[DomainAlert]:
        """Un agent ne doit pas avoir plusieurs états le même jour."""
        alerts = []
        seen = set()

        for e in etats:
            key = (e.agent_id, e.jour)
            if key in seen:
                alerts.append(DomainAlert(
                    f"Doublon d'état pour agent {e.agent_id} le {e.jour}",
                    Severity.ERROR,
                    source="EtatJourAgentValidatorService"
                ))
            seen.add(key)
        return alerts

    def _check_type(self, e: EtatJourAgent) -> List[DomainAlert]:
        """Vérifie que le type_jour est un membre valide de l’enum."""
        alerts = []
        try:
            if not isinstance(e.type_jour, TypeJour):
                TypeJour(e.type_jour)
        except Exception:
            alerts.append(DomainAlert(
                f"Type d'état inconnu : '{e.type_jour}'",
                Severity.ERROR,
                source="EtatJourAgentValidatorService"
            ))
        return alerts

    def _check_coherence(self, e: EtatJourAgent) -> List[DomainAlert]:
        """Vérifie les champs obligatoires."""
        alerts = []

        if not e.agent_id:
            alerts.append(DomainAlert("État sans agent_id.", Severity.ERROR, source="EtatJourAgentValidatorService"))
        if not e.jour:
            alerts.append(DomainAlert("État sans date définie.", Severity.ERROR, source="EtatJourAgentValidatorService"))
        if not e.type_jour:
            alerts.append(DomainAlert("État sans type_jour.", Severity.ERROR, source="EtatJourAgentValidatorService"))

        return alerts

    # ---------------------------------------------------------
    # 🔹 Validation unitaire
    # ---------------------------------------------------------
    def validate(self, e: EtatJourAgent) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_type(e))
        alerts.extend(self._check_coherence(e))
        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts

    # ---------------------------------------------------------
    # 🔹 Validation globale
    # ---------------------------------------------------------
    def validate_all(self, etats: List[EtatJourAgent]) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_doublons(etats))

        for e in etats:
            _, local = self.validate(e)
            alerts.extend(local)

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts
