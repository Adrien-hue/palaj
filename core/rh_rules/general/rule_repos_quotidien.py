# core/rh_rules/rule_repos_quotidien.py
from typing import List, Tuple

from core.rh_rules.day_rule import DayRule
from core.utils.domain_alert import DomainAlert
from core.utils.time_helpers import minutes_to_duree_str
from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay


class ReposQuotidienRule(DayRule):
    """
    Règle RH : Respect du repos quotidien minimal entre deux journées travaillées.
      - Repos minimal : 12h20 (740 minutes)
      - Repos minimal si travail de nuit : 14h00 (840 minutes)

    La règle est évaluée pour chaque WorkDay travaillé, en regardant le repos
    depuis la précédente journée travaillée.
    """

    name = "ReposQuotidienRule"
    description = "Vérifie le respect du repos quotidien minimal entre deux jours travaillés."

    REPOS_MIN_STANDARD_MIN = 12 * 60 + 20   # 12h20
    REPOS_MIN_NUIT_MIN = 14 * 60           # 14h00

    def check_day(
        self,
        context: PlanningContext,
        work_day: WorkDay,
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        jour = work_day.jour

        # Jour non travaillé → règle non applicable
        if work_day.is_rest() or not work_day.is_working():
            return True, []

        # Durée de repos en minutes depuis le dernier jour travaillé
        repos_minutes = context.get_repos_minutes_since_last_work_day(jour)
        if repos_minutes is None:
            # Pas de jour travaillé précédent, ou pas de tranches valides → rien à contrôler
            return True, []

        # --- Calcul du repos minimum requis ---
        prev_wd = context.get_previous_working_day(jour)
        requires_night_rest = False

        if prev_wd and not prev_wd.is_rest():
            # Si la veille ou le jour courant est nocturne → repos de nuit requis
            requires_night_rest = prev_wd.is_nocturne() or work_day.is_nocturne()

        repos_min = (
            self.REPOS_MIN_NUIT_MIN
            if requires_night_rest
            else self.REPOS_MIN_STANDARD_MIN
        )

        # --- Comparaison et alerte ---
        if repos_minutes < repos_min:
            alerts.append(
                self.error(
                    msg=(
                        "Repos quotidien insuffisant : "
                        f"{minutes_to_duree_str(repos_minutes)} < "
                        f"{minutes_to_duree_str(repos_min)}"
                    ),
                    jour=jour,
                    code="REPOS_QUOTIDIEN_INSUFFISANT",
                )
            )

        return len(alerts) == 0, alerts
