# core/rh_rules/rh_rules_engine.py
from datetime import timedelta
from typing import List, Tuple

from core.utils.domain_alert import DomainAlert, Severity
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.domain.contexts.planning_context import PlanningContext


class RHRulesEngine:
    """
    Moteur centralisant et exécutant toutes les règles RH sur un PlanningContext.
    """

    def __init__(self, rules: List[BaseRule] | None = None, verbose: bool = True):
        # Si aucune règle n'est passée, on peut charger un set de base par défaut
        self.rules = rules or []
        self.verbose = verbose

    def register_rule(self, rule: BaseRule):
        """Ajoute une règle RH au moteur."""
        self.rules.append(rule)

    def list_rules(self) -> List[str]:
        """Retourne la liste des règles enregistrées (pour debug / affichage)."""
        return [f"{r.name} ({r.scope.name})" for r in self.rules]
    
    def run_for_context(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        """
        Exécute l'ensemble des règles RH pour un agent donné
        (planning complet ou journée unique selon `context`).
        """
        all_alerts: List[DomainAlert] = []

        if not context.work_days:
            return True, []

        # ✅ Cas 2 : boucle sur la période complète
        for wd in context.work_days:
            context.set_date_reference(wd.jour)
            _, alerts = self._run_rules_for_day(context)
            all_alerts.extend(alerts)

        # ✅ Cas 3 : règles "période" (ex: GPT)
        for rule in self.rules:
            if rule.scope == RuleScope.PERIOD:
                _, period_alerts = rule.check(context)
                all_alerts.extend(period_alerts)

        # Résumé global
        is_valid = all(a.severity != Severity.ERROR for a in all_alerts)

        if self.verbose:
            self._print_summary_report(is_valid, all_alerts)

        return is_valid, all_alerts

    # -----------------------------------------------------------
    def _run_rules_for_day(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        """
        Exécute les règles quotidiennes (non marquées `is_period_rule`)
        pour la date contenue dans `context.date_reference`.
        """
        day_alerts: List[DomainAlert] = []

        for rule in self.rules:
            if rule.scope == RuleScope.PERIOD:
                continue  # on ignore les règles multi-jours ici

            _, rule_alerts = rule.check(context)

            day_alerts.extend(rule_alerts)

        is_valid = all(a.severity != Severity.ERROR for a in day_alerts)
        return is_valid, day_alerts

    def _print_summary_report(self, is_valid: bool, alerts: List[DomainAlert]):
        """Affiche un résumé global des résultats."""
        if not self.verbose:
            return

        print("\n===== RAPPORT GLOBAL RÈGLES RH =====")
        if is_valid:
            print("✅ Aucune erreur bloquante détectée.")
        else:
            print("🚨 Des non-conformités ont été détectées :")

        for a in alerts:
            prefix = {
                Severity.INFO: "[INFO]",
                Severity.WARNING: "[WARN]",
                Severity.ERROR: "[ERROR]",
            }.get(a.severity, "[UNK]")

            jour_str = f"[{a.jour}]" if a.jour else ""
            print(f" {prefix} {jour_str} {a.message} (src: {a.source})")

        print("====================================\n")
