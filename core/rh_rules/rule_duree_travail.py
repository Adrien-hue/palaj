# core/rh_rules/rule_duree_travail.py
from datetime import time
from typing import List, Tuple

from core.rh_rules.base_rule import BaseRule
from core.utils.domain_alert import DomainAlert, Severity
from core.utils.time_helpers import minutes_to_duree_str
from core.domain.contexts.planning_context import PlanningContext


class DureeTravailRule(BaseRule):
    """
    Règle RH : durée minimale et maximale de travail par jour.
    - Minimum : 5h30 (330 min)
    - Maximum : 10h (600 min)
    - Maximum de nuit : 8h30 (510 min)
    """

    name = "duree_travail"
    description = "Durée journalière de travail (min/max selon travail de nuit)"

    DUREE_MIN_MIN = 5.5 * 60   # 5h30 → 330 min
    DUREE_MAX_MIN = 10 * 60    # 10h → 600 min
    DUREE_MAX_NUIT_MIN = 8.5 * 60  # 8h30 → 510 min
    HEURE_NUIT_DEBUT = time(21, 30)
    HEURE_NUIT_FIN = time(6, 30)

    # -----------------------------------------------------
    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        jour = context.date_reference

        if jour is None:
            alerts.append(
                DomainAlert(
                    "Date de référence manquante dans le contexte.",
                    Severity.ERROR,
                    source=self.name,
                )
            )
            return False, alerts

        wd = context.get_work_day(jour)
        if not wd or not wd.is_working():
            # Pas de travail → pas de vérification
            return True, []

        # Récupération de la durée de travail réelle
        total_minutes = wd.duree_minutes()
        
        # Détection du travail de nuit
        travail_nuit = wd.is_nocturne()
        max_allowed = self.DUREE_MAX_NUIT_MIN if travail_nuit else self.DUREE_MAX_MIN

        # Vérifications
        if total_minutes < self.DUREE_MIN_MIN:
            alerts.append(
                DomainAlert(
                    f"Durée de travail insuffisante : "
                    f"{minutes_to_duree_str(total_minutes)} < {minutes_to_duree_str(int(self.DUREE_MIN_MIN))}",
                    Severity.WARNING,
                    jour=jour,
                    source=self.name,
                )
            )

        if total_minutes > max_allowed:
            alerts.append(
                DomainAlert(
                    f"Durée de travail excessive : "
                    f"{minutes_to_duree_str(total_minutes)} > {minutes_to_duree_str(int(max_allowed))}",
                    Severity.WARNING,
                    jour=jour,
                    source=self.name,
                )
            )

        return len(alerts) == 0, alerts