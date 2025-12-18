from typing import List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from core.domain.entities.regime import Regime


class RegimeValidatorService:
    """
    Service de domaine : validation métier pure des régimes.
    Ne dépend pas de la base de données.
    """

    # =========================================================
    # 🔹 Vérifications internes
    # =========================================================
    def _check_doublons(self, regimes: List[Regime]) -> List[DomainAlert]:
        """Vérifie qu'aucun ID ni nom de régime n'est dupliqué."""
        alerts: List[DomainAlert] = []
        seen_ids = set()
        seen_names = set()

        for r in regimes:
            if r.id in seen_ids:
                alerts.append(DomainAlert(
                    f"Doublon de régime ID {r.id} ({r.nom})",
                    Severity.ERROR,
                    source="RegimeValidatorService"
                ))
            seen_ids.add(r.id)

            normalized_name = r.nom.strip().lower()
            if normalized_name in seen_names:
                alerts.append(DomainAlert(
                    f"Doublon de nom de régime : {r.nom}",
                    Severity.ERROR,
                    source="RegimeValidatorService"
                ))
            seen_names.add(normalized_name)

        return alerts

    def _check_duree_moyenne(self, regime: Regime) -> List[DomainAlert]:
        """Vérifie que la durée moyenne de journée est cohérente."""
        alerts: List[DomainAlert] = []
        d = getattr(regime, "duree_moyenne_journee_service_min", 0)
        
        if d is None or d <= 0:
            alerts.append(DomainAlert(
                f"Régime {regime.nom} a une durée moyenne non définie ou invalide ({d}).",
                Severity.ERROR,
                source="RegimeValidatorService"
            ))
        elif d > 1440:
            alerts.append(DomainAlert(
                f"Régime {regime.nom} a une durée moyenne impossible (> 24h).",
                Severity.ERROR,
                source="RegimeValidatorService"
            ))

        return alerts

    def _check_repos_annuels(self, regime: Regime) -> List[DomainAlert]:
        """Vérifie que le nombre de repos annuels est cohérent."""
        alerts: List[DomainAlert] = []
        repos = getattr(regime, "repos_periodiques_annuels", 0)
        if repos is None or repos <= 0:
            alerts.append(DomainAlert(
                f"Régime {regime.nom} a un nombre de repos annuel invalide ({repos}).",
                Severity.WARNING,
                source="RegimeValidatorService"
            ))
        elif repos > 365:
            alerts.append(DomainAlert(
                f"Régime {regime.nom} dépasse 365 jours de repos annuels.",
                Severity.ERROR,
                source="RegimeValidatorService"
            ))
        return alerts

    # =========================================================
    # 🔹 Validation unitaire
    # =========================================================
    def validate(self, regime: Regime) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_duree_moyenne(regime))
        alerts.extend(self._check_repos_annuels(regime))
        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts

    # =========================================================
    # 🔹 Validation globale
    # =========================================================
    def validate_all(self, regimes: List[Regime]) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_doublons(regimes))

        for r in regimes:
            _, local_alerts = self.validate(r)
            alerts.extend(local_alerts)

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)
        return is_valid, alerts