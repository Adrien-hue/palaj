# services/tranche_service.py
from typing import List, Tuple

from core.utils.domain_alert import DomainAlert, Severity
from core.utils.logger import Logger

from core.domain.entities import Tranche

from db.repositories.tranche_repo import TrancheRepository


class TrancheService:
    """
    Service métier gérant la logique RH et la validation des tranches.
    """

    def __init__(self, tranche_repo: TrancheRepository, verbose: bool = False):
        self.tranche_repo = tranche_repo

        self.logger = Logger(verbose=verbose)

    # -------------
    # Vérifications
    # -------------
    def _check_doublons(self, tranches: List[Tranche]) -> List[DomainAlert]:
        """Détecte les doublons d'ID de tranches."""
        alerts: List[DomainAlert] = []
        seen = set()
        for t in tranches:
            if t.id in seen:
                alert = DomainAlert(
                    f"Doublon de tranche ID {t.id} ({t.abbr})",
                    Severity.ERROR,
                    source="TrancheService",
                )
                alerts.append(alert)
            seen.add(t.id)
        return alerts
    
    def _check_duree(self, tranches: List[Tranche]) -> List[DomainAlert]:
        """
        Vérifie que la durée d'une tranche est cohérente :
        - horaires présents
        - durée > 0
        - durée ≤ 11h
        - pas d'incohérence horaire (fin avant début sans passage minuit explicite)
        - pas de durée anormale (> 24h)
        """
        alerts: List[DomainAlert] = []

        for t in tranches:
            # Vérif présence horaire
            if not (t.debut and t.fin):
                alerts.append(
                    DomainAlert(
                        f"Tranche {t.abbr} a des horaires incomplets.",
                        Severity.ERROR,
                        source="TrancheService",
                    )
                )
                continue

            # Calcule durée (en heures)
            duree_h = t.duree()

            # Cas 1 : Fin avant début (et pas de passage minuit)
            if duree_h < 0:
                alerts.append(
                    DomainAlert(
                        f"Tranche {t.abbr} incohérente : fin ({t.fin}) avant début ({t.debut}).",
                        Severity.ERROR,
                        source="TrancheService",
                    )
                )
                continue

            # Cas 2 : Durée nulle
            if duree_h == 0:
                alerts.append(
                    DomainAlert(
                        f"Tranche {t.abbr} a une durée nulle.",
                        Severity.ERROR,
                        source="TrancheService",
                    )
                )
                continue

            # Cas 3 : Durée > 24h (erreur de saisie manifeste)
            if duree_h > 24:
                alerts.append(
                    DomainAlert(
                        f"Tranche {t.abbr} a une durée impossible ({t.duree_formatee()}).",
                        Severity.ERROR,
                        source="TrancheService",
                    )
                )
                continue

            # Cas 4 : Durée > 11h = avertissement RH
            if duree_h > 11:
                alerts.append(
                    DomainAlert(
                        f"Tranche {t.abbr} dépasse 11h d'amplitude ({t.duree_formatee()}).",
                        Severity.WARNING,
                        source="TrancheService",
                    )
                )

        return alerts

    def _check_nb_agents_requis(self, tranches: List[Tranche]) -> List[DomainAlert]:
        """Vérifie que chaque tranche demande au moins un agent."""
        alerts: List[DomainAlert] = []
        for t in tranches:
            if t.nb_agents_requis <= 0:
                alert = DomainAlert(
                    f"Tranche {t.abbr} a un nb_agents_requis invalide ({t.nb_agents_requis})",
                    Severity.ERROR,
                    source="TrancheService",
                )
                alerts.append(alert)
        return alerts
    
    # ------------
    # Validations
    # ------------
    def validate(self, tranche: Tranche) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide une tranche unique.
        Retourne : (is_valid, alerts)
        """
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_nb_agents_requis([tranche]))
        alerts.extend(self._check_duree([tranche]))

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)

        for a in alerts:
            self.logger.log_from_alert(a)

        return is_valid, alerts

    def validate_by_id(self, tranche_id: int) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide une tranche spécifique par ID.
        """
        tranche = self.tranche_repo.get(tranche_id)
        if not tranche:
            alert = DomainAlert(
                f"Tranche introuvable (ID={tranche_id})",
                Severity.ERROR,
                source="TrancheService",
            )
            self.logger.log_from_alert(alert)
            return False, [alert]
        return self.validate(tranche)

    def validate_all(self) -> Tuple[bool, List[DomainAlert]]:
        """
        Valide toutes les tranches du dépôt.
        """
        tranches = self.tranche_repo.list_all()
        alerts: List[DomainAlert] = []
        alerts.extend(self._check_doublons(tranches))
        alerts.extend(self._check_nb_agents_requis(tranches))
        alerts.extend(self._check_duree(tranches))

        for a in alerts:
            self.logger.log_from_alert(a)

        is_valid = not any(a.severity == Severity.ERROR for a in alerts)

        if is_valid:
            self.logger.success("✅ Toutes les tranches sont valides.")
        else:
            self.logger.warn("⚠️ Certaines tranches présentent des incohérences.")

        return is_valid, alerts