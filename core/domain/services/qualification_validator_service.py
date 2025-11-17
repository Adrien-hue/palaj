from datetime import date
from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.entities.qualification import Qualification


class QualificationValidatorService:
    """
    Service de domaine : validation métier pure des qualifications.
    Ne dépend d'aucune base de données ni repository.
    """

    # =========================================================
    # 🔹 Vérifications internes
    # =========================================================
    def _check_doublons(self, qualifications: List[Qualification]) -> List[DomainAlert]:
        """Détecte les doublons (même agent et même poste)."""
        alerts: List[DomainAlert] = []
        seen_pairs = set()

        for q in qualifications:
            key = (q.agent_id, q.poste_id)
            if key in seen_pairs:
                alerts.append(DomainAlert(
                    f"Doublon de qualification : agent {q.agent_id} déjà qualifié pour le poste {q.poste_id}.",
                    Severity.ERROR,
                    source="QualificationValidatorService"
                ))
            seen_pairs.add(key)

        return alerts

    def _check_coherence(self, q: Qualification) -> List[DomainAlert]:
        """Vérifie la cohérence d'une qualification unique."""
        alerts: List[DomainAlert] = []

        if not q.agent_id:
            alerts.append(DomainAlert(
                f"Qualification sans agent associée (poste {q.poste_id}).",
                Severity.ERROR,
                source="QualificationValidatorService"
            ))

        if not q.poste_id:
            alerts.append(DomainAlert(
                f"Qualification sans poste associé (agent {q.agent_id}).",
                Severity.ERROR,
                source="QualificationValidatorService"
            ))

        if q.date_qualification:
            today = date.today()
            if q.date_qualification > today:
                alerts.append(DomainAlert(
                    f"Qualification future détectée pour l’agent {q.agent_id} (poste {q.poste_id}, date {q.date_qualification}).",
                    Severity.WARNING,
                    source="QualificationValidatorService"
                ))

            # (optionnel) on pourrait aussi fixer une borne max — ex. 1950
            if q.date_qualification.year < 1950:
                alerts.append(DomainAlert(
                    f"Date de qualification incohérente pour l’agent {q.agent_id} ({q.date_qualification}).",
                    Severity.WARNING,
                    source="QualificationValidatorService"
                ))

        return alerts

    # =========================================================
    # 🔹 Validation unitaire
    # =========================================================
    def validate(self, qualification: Qualification) -> Tuple[bool, List[DomainAlert]]:
        alerts = self._check_coherence(qualification)
        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts

    # =========================================================
    # 🔹 Validation globale
    # =========================================================
    def validate_all(self, qualifications: List[Qualification]) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_doublons(qualifications))

        for q in qualifications:
            _, local_alerts = self.validate(q)
            alerts.extend(local_alerts)

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts
