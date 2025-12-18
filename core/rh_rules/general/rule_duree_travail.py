# core/rh_rules/rule_duree_travail.py

from typing import List, Tuple

from core.rh_rules.day_rule import DayRule
from core.utils.domain_alert import DomainAlert
from core.utils.time_helpers import minutes_to_duree_str
from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay


class DureeTravailRule(DayRule):
    """
    Règle RH : durée minimale et maximale de travail par jour.
    - Minimum : 5h30 (330 min)
    - Maximum : 10h (600 min)
    - Maximum de nuit : 8h30 (510 min)
    """

    name = "DureeTravailRule"
    description = "Durée journalière de travail (min/max selon travail de nuit)."

    DUREE_MIN_MIN = 5.5 * 60        # 5h30 → 330 min
    DUREE_MAX_MIN = 10 * 60         # 10h   → 600 min
    DUREE_MAX_NUIT_MIN = 8.5 * 60   # 8h30 → 510 min

    def check_day(
        self,
        context: PlanningContext,
        work_day: WorkDay,
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        # Pas de travail → pas de vérification
        if not work_day.is_working():
            return True, []

        # Durée réelle travaillée sur la journée
        total_minutes = work_day.duree_minutes()

        # Détection du travail de nuit déléguée au WorkDay
        travail_nuit = work_day.is_nocturne()
        max_allowed = (
            self.DUREE_MAX_NUIT_MIN if travail_nuit else self.DUREE_MAX_MIN
        )

        # Vérif durée minimale
        if total_minutes < self.DUREE_MIN_MIN:
            alerts.append(
                self.error(
                    msg=(
                        "Durée de travail insuffisante : "
                        f"{minutes_to_duree_str(int(total_minutes))} < "
                        f"{minutes_to_duree_str(int(self.DUREE_MIN_MIN))}"
                    ),
                    jour=work_day.jour,
                    code="DUREE_TRAVAIL_MIN_INSUFFISANTE",
                )
            )

        # Vérif durée maximale (ou max nuit)
        if total_minutes > max_allowed:
            alerts.append(
                self.error(
                    msg=(
                        "Durée de travail excessive : "
                        f"{minutes_to_duree_str(int(total_minutes))} > "
                        f"{minutes_to_duree_str(int(max_allowed))}"
                    ),
                    jour=work_day.jour,
                    code=(
                        "DUREE_TRAVAIL_MAX_NUIT_DEPASSEE"
                        if travail_nuit
                        else "DUREE_TRAVAIL_MAX_DEPASSEE"
                    ),
                )
            )

        return len(alerts) == 0, alerts
