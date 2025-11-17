# core/domain/services/tranche_validator_service.py

from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.entities.tranche import Tranche


class TrancheValidatorService:
    """
    Service de domaine : validation métier pure des tranches.
    Ne dépend d'aucune base de données ni repository.
    """

    # -------------------------------------------------------
    # 🔹 Vérifications internes
    # -------------------------------------------------------
    def _check_doublons(self, tranches: List[Tranche]) -> List[DomainAlert]:
        """Détecte les doublons d’ID de tranches."""
        alerts: List[DomainAlert] = []
        seen = set()
        for t in tranches:
            if t.id in seen:
                alerts.append(DomainAlert(
                    f"Doublon de tranche ID {t.id} ({t.nom})",
                    Severity.ERROR,
                    source="TrancheValidatorService"
                ))
            seen.add(t.id)
        return alerts

    def _check_duree(self, tranche: Tranche) -> List[DomainAlert]:
        """Vérifie la cohérence horaire et la durée des tranches."""
        alerts: List[DomainAlert] = []

        if not (tranche.heure_debut and tranche.heure_fin):
            alerts.append(DomainAlert(
                f"Tranche {tranche.nom} a des horaires incomplets.",
                Severity.ERROR,
                source="TrancheValidatorService"
            ))

        duree_h = tranche.duree()

        # Erreurs
        if duree_h < 0:
            alerts.append(DomainAlert(
                f"Tranche {tranche.nom} incohérente : fin ({tranche.heure_fin}) avant début ({tranche.heure_debut}).",
                Severity.ERROR,
                source="TrancheValidatorService"
            ))

        if duree_h == 0:
            alerts.append(DomainAlert(
                f"Tranche {tranche.nom} a une durée nulle.",
                Severity.ERROR,
                source="TrancheValidatorService"
            ))

        if duree_h > 24:
            alerts.append(DomainAlert(
                f"Tranche {tranche.nom} a une durée impossible ({tranche.duree_formatee()}).",
                Severity.ERROR,
                source="TrancheValidatorService"
            ))

        # Avertissement RH
        if duree_h > 11:
            alerts.append(DomainAlert(
                f"Tranche {tranche.nom} dépasse 11h d’amplitude ({tranche.duree_formatee()}).",
                Severity.WARNING,
                source="TrancheValidatorService"
            ))

        return alerts
    
    def _check_poste_associe(self, tranche: Tranche) -> List[DomainAlert]:
        """Vérifie qu'une tranche est bien liée à un poste."""
        alerts: List[DomainAlert] = []
        if tranche.poste_id is None:
            alerts.append(DomainAlert(
                f"Tranche {tranche.nom} n'est associée à aucun poste.",
                Severity.ERROR,
                source="TrancheValidatorService"
            ))
        return alerts

    # -------------------------------------------------------
    # 🔹 Validation principale
    # -------------------------------------------------------
    def validate(self, tranche: Tranche) -> Tuple[bool, List[DomainAlert]]:
        """Valide une tranche."""
        alerts = []
        alerts.extend(self._check_duree(tranche))
        alerts.extend(self._check_poste_associe(tranche))

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts

    def validate_all(self, tranches: List[Tranche]) -> Tuple[bool, List[DomainAlert]]:
        """Valide toutes les tranches."""
        alerts = []
        alerts.extend(self._check_doublons(tranches))
        for t in tranches:
            _, t_alerts = self.validate(t)
            alerts.extend(t_alerts)
        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts