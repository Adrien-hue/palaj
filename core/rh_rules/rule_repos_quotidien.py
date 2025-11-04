# core/rh_rules/rule_repos_quotidien.py
from typing import List, Tuple

from core.rh_rules.base_rule import BaseRule
from core.utils.domain_alert import DomainAlert, Severity
from core.utils.time_helpers import minutes_to_duree_str
from core.domain.contexts.planning_context import PlanningContext


class ReposQuotidienRule(BaseRule):
    """
    Règle RH : Respect du repos quotidien minimal entre deux journées travaillées.
      - Repos minimal : 12h20 (740 minutes)
      - Repos minimal si travail de nuit : 14h00 (840 minutes)
    """

    name = "repos_quotidien"
    description = "Vérifie le respect du repos quotidien minimal entre deux jours travaillés."

    REPOS_MIN_STANDARD_MIN = 12 * 60 + 20   # 12h20
    REPOS_MIN_NUIT_MIN = 14 * 60            # 14h00

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        jour = context.date_reference
        if not jour:
            return True, []

        wd = context.get_work_day(jour)
        if not wd or wd.is_rest():
            return True, []  # pas de travail ce jour-là

        repos_minutes = context.get_repos_minutes_since_last_work_day(jour)
        if repos_minutes is None:
            return True, []  # pas de jour précédent ou pas de tranches valides

        # --- Calcul du repos minimum requis
        requires_night_rest = False

        prev_wd = context.get_previous_working_day(jour)

        if prev_wd and not prev_wd.is_rest():
            requires_night_rest = prev_wd.is_nocturne() or wd.is_nocturne()

        repos_min = (
            self.REPOS_MIN_NUIT_MIN if requires_night_rest else self.REPOS_MIN_STANDARD_MIN
        )

        # --- Comparaison et alerte
        if repos_minutes < repos_min:
            alerts.append(
                DomainAlert(
                    f"Repos quotidien insuffisant : "
                    f"{minutes_to_duree_str(repos_minutes)} < {minutes_to_duree_str(repos_min)}",
                    Severity.ERROR,
                    jour=jour,
                    source=self.name,
                )
            )

        return len(alerts) == 0, alerts
