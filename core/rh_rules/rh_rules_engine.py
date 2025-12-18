# core/rh_rules/rh_rules_engine.py

from typing import Dict, List, Tuple
from core.utils.domain_alert import DomainAlert, Severity
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.domain.contexts.planning_context import PlanningContext


class RHRulesEngine:
    """
    Moteur centralisant et exécutant toutes les règles RH sur un PlanningContext.
    """

    def __init__(self, rules: List[BaseRule] | None = None):
        self.rules: List[BaseRule] = rules or []

    # -----------------------------------------------------------
    def register_rule(self, rule: BaseRule):
        self.rules.append(rule)

    def list_rules(self) -> List[str]:
        return [f"{r.name} ({r.scope.name})" for r in self.rules]

    # -----------------------------------------------------------
    def run_for_context(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        """
        Exécute :
        - les règles journalières (DAY)
        - les règles multi-jours (PERIOD)
        """

        if not context.work_days:
            return True, []

        all_alerts: List[DomainAlert] = []

        # --- 1) Exécution JOUR PAR JOUR ---
        # On s'assure d'un parcours chronologique (au cas où work_days ne le sont pas déjà).
        for wd in sorted(context.work_days, key=lambda d: d.jour):
            # Le moteur fixe le jour et le WorkDay de référence pour les règles DAY
            context.set_date_reference(wd.jour)

            context.set_current_work_day(wd)

            _, day_alerts = self._run_rules_for_day(context)
            all_alerts.extend(day_alerts)

        # Optionnel : nettoyer les références après coup
        context.set_date_reference(None)
        context.set_current_work_day(None)

        # --- 2) Exécution des règles sur PÉRIODE ---
        for rule in self.rules:
            if rule.scope is RuleScope.PERIOD and rule.applies_to(context):
                _, alerts = rule.check(context)
                all_alerts.extend(alerts)

        # --- 3) Agrégation ---
        is_valid = all(a.severity != Severity.ERROR for a in all_alerts)

        return is_valid, all_alerts

    # -----------------------------------------------------------
    def _run_rules_for_day(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        """
        Exécute uniquement les règles de niveau JOUR (scope == DAY)
        pour le WorkDay actuellement positionné par le moteur
        dans le PlanningContext.
        """
        alerts: List[DomainAlert] = []

        for rule in self.rules:
            # On ne touche pas aux règles période ici
            if rule.scope is RuleScope.PERIOD:
                continue
            if not rule.applies_to(context):
                continue

            _, rule_alerts = rule.check(context)
            alerts.extend(rule_alerts)

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts