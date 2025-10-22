# services/tranche_service.py
from typing import List, Tuple

from core.utils.logger import Logger

from models.tranche import Tranche

from db.repositories.tranche_repo import TrancheRepository


class TrancheService:
    """
    Service métier gérant la logique RH et la validation des tranches.
    """

    def __init__(self, tranche_repo: TrancheRepository, verbose: bool = False):
        self.tranche_repo = tranche_repo

        self.logger = Logger(verbose=verbose)

    def check_doublons(self, tranche: List[Tranche]) -> List[str]:
        """Détecte les doublons de tranches."""
        alerts = []
        
        seen_ids = set()

        for t in tranche:
            if t.id in seen_ids:
                alerts.append(f"❌ Doublon de tranche ID {t.id} ({t.abbr})")
            seen_ids.add(t.id)
        return alerts

    def check_nb_agents_requis(self, tranche: Tranche) -> List[str]:
        """Vérifie que chaque tranche demande au moins un agent."""
        alerts = []

        if tranche.nb_agents_requis <= 0:
            alerts.append(f"❌ Tranche {tranche.abbr} a un nb_agents_requis invalide ({tranche.nb_agents_requis})")
        return alerts

    def check_duree(self, tranche: Tranche) -> List[str]:
        """Vérifie que la durée de la tranche est valide (non nulle et <= 11h)."""
        alerts = []

        if tranche.debut and tranche.fin:
            d = tranche.duree()
            if d == 0:
                alerts.append(f"❌ Tranche {tranche.abbr} a une durée nulle.")
            elif d > 11:
                alerts.append(f"⚠️ Tranche {tranche.abbr} dépasse 11h d'amplitude ({tranche.duree_formatee()})")
        return alerts
    
    # ------------
    # Validations
    # ------------
    def validate(self, tranche: Tranche) -> Tuple[bool, List[str]]:
        """Valide une tranche en exécutant toutes les vérifications."""
        alerts = []
        alerts.extend(self.check_nb_agents_requis(tranche))
        alerts.extend(self.check_duree(tranche))
        return (len(alerts) == 0, alerts)

    def validate_by_id(self, tranche_id: int) -> Tuple[bool, List[str]]:
        """Valide une tranche par son ID."""
        tranche = self.tranche_repo.get(tranche_id)
        if not tranche:
            self.logger.warn(f"Tranche avec ID {tranche_id} non trouvée.")
            return (False, [f"❌ Tranche avec ID {tranche_id} non trouvée."])
        return self.validate(tranche)

    def validate_all(self) -> Tuple[bool, List[str]]:
        """Exécute toutes les validations et retourne la liste complète des alertes."""
        list_tranches = self.tranche_repo.list_all()
        alerts = []
        alerts.extend(self.check_doublons(list_tranches))
        for t in list_tranches:
            _, alerts = self.validate(t)
            alerts.extend(alerts)

        if len(alerts) == 0:
            self.logger.success(f"Toutes les tranches sont valides.")
        else:
            self.logger.warn(f"🚨 Problèmes détectés dans les tranches :")
            for a in alerts:
                self.logger.warn("  - " + a)
        return (len(alerts) == 0, alerts)