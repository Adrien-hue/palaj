# core/rh_rules/rule_repos_qualifie_info.py
from typing import List, Tuple
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity
from core.utils.time_helpers import minutes_to_duree_str
from core.domain.contexts.planning_context import PlanningContext
from core.application.services.planning.periode_repos_analyzer import PeriodeReposAnalyzer

class ReposQualifieInfoRule(BaseRule):
    """
    Règle informative : identifie et qualifie toutes les périodes de repos (RP simple, double, triple, etc.)
    quelle que soit leur position dans le planning.
    """

    name = "repos_qualifie_info"
    description = "Détection et qualification des périodes de repos continues."
    scope = RuleScope.PERIOD

    def __init__(self):
        self.service = PeriodeReposAnalyzer()

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []
        periodes = self.service.detect(context)
        
        if not periodes:
            return True, []

        for pr in periodes:
            alerts.append(
                DomainAlert(
                    f"{pr.label()} détecté du {pr.start} au {pr.end} "
                    f"({minutes_to_duree_str(pr.duree_minutes)}).",
                    Severity.INFO,
                    jour=pr.start,
                    source=self.name,
                )
            )

        return True, alerts
