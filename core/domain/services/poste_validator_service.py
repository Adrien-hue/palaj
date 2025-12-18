from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.entities.poste import Poste


class PosteValidatorService:
    """
    Service de domaine : validation métier pure des postes.
    Sépare les vérifications internes (doublons, tranches, qualifications)
    et expose deux méthodes publiques :
      - validate(poste)
      - validate_all(postes)
    """

    # =========================================================
    # 🔹 Vérifications internes (unitaires ou globales)
    # =========================================================

    def _check_doublons(self, postes: List[Poste]) -> List[DomainAlert]:
        """Détecte les doublons d'ID parmi tous les postes."""
        alerts: List[DomainAlert] = []
        seen_ids = set()
        for p in postes:
            if p.id in seen_ids:
                alerts.append(DomainAlert(
                    f"Doublon de poste ID {p.id}",
                    Severity.ERROR,
                    source="PosteValidatorService"
                ))
            seen_ids.add(p.id)
        return alerts

    def _check_tranches(self, poste: Poste) -> List[DomainAlert]:
        """Vérifie qu’un poste possède au moins une tranche."""
        alerts: List[DomainAlert] = []
        tranches = getattr(poste, "tranches", [])
        if not tranches or len(tranches) == 0:
            alerts.append(DomainAlert(
                f"Le poste {poste.nom} n’a aucune tranche associée.",
                Severity.WARNING,
                source="PosteValidatorService"
            ))
        return alerts

    def _check_qualifications(self, poste: Poste) -> List[DomainAlert]:
        """Vérifie la cohérence des qualifications associées à un poste."""
        alerts: List[DomainAlert] = []
        if poste.qualifications is not None:
            for q in poste.qualifications:
                if q.poste_id != poste.id:
                    alerts.append(DomainAlert(
                        f"Qualification incohérente pour le poste {poste.nom} (poste_id={q.poste_id})",
                        Severity.WARNING,
                        source="PosteValidatorService"
                    ))
        else:
            alerts.append(DomainAlert(
                f"Aucune qualification pour le poste {poste.nom} (poste_id={poste.id})",
                Severity.WARNING,
                source="PosteValidatorService"
            ))
        return alerts

    # =========================================================
    # 🔹 Validation unitaire
    # =========================================================
    def validate(self, poste: Poste) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide un poste unique (sans vérifier les doublons entre postes).
        Vérifie :
          - qu’il possède au moins une tranche
          - la cohérence de ses qualifications
        """
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_tranches(poste))
        alerts.extend(self._check_qualifications(poste))

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts

    # =========================================================
    # 🔹 Validation globale
    # =========================================================
    def validate_all(self, postes: List[Poste]) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide l’ensemble des postes :
          - détecte les doublons d’ID
          - exécute la validation unitaire sur chacun
        """
        alerts: List[DomainAlert] = []

        # Vérification des doublons (globale, exécutée une seule fois)
        alerts.extend(self._check_doublons(postes))

        # Vérifications locales sur chaque poste
        for p in postes:
            _, local_alerts = self.validate(p)
            alerts.extend(local_alerts)

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts
