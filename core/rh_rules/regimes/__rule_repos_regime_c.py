# core/rh_rules/rule_repos_regime_c.py
from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.year_rule import YearRule
from core.utils.domain_alert import DomainAlert, Severity
from core.application.services.planning.repos_stats_analyzer import ReposStatsAnalyzer


class RegimeCReposRule(YearRule):
    """
    Règle spécifique au régime C (regime_id = 2).

    Exigences (par année civile complète) :
    - Au moins 118 jours de repos périodiques (RP)
    - Dont 52 dimanches de repos
    """

    name = "RegimeCReposRule"
    description = "Repos annuels spécifiques au régime C (118 RP / 52 dimanches)."

    MIN_RP_ANNUELS = 118
    MIN_RP_DIMANCHES = 52

    def __init__(self, analyzer: ReposStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or ReposStatsAnalyzer()

    # ---------------------------------------------------------
    # Applicabilité de la règle
    # ---------------------------------------------------------
    def applies_to(self, context: PlanningContext) -> bool:
        """
        La règle ne s'applique qu'aux agents de régime C (regime_id = 2).
        Si l'agent n'a pas de regime_id, on considère que la règle ne s'applique pas.
        """
        regime_id = getattr(context.agent, "regime_id", None)
        return regime_id == 2

    # On surcharge check pour court-circuiter si le régime n'est pas C,
    # puis on délègue à YearRule.check pour le découpage par année.
    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        if not self.applies_to(context):
            return True, []
        return super().check(context)

    # ---------------------------------------------------------
    # Implémentation annuelle
    # ---------------------------------------------------------
    def check_year(
        self,
        context: PlanningContext,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        # Aucun jour dans cette année pour cet agent → info et on sort
        if not work_days:
            alerts.append(
                self.info(
                    msg=f"[{year}] Aucun jour planifié pour cet agent en régime C.",
                    code="REGIME_C_EMPTY_YEAR",
                )
            )
            return True, alerts

        # 1) Statistiques de repos pour CETTE année
        repos_summary = self.analyzer.summarize_workdays(work_days)

        # 2) Résumé informatif systématique
        summary_msg = (
            f"[{year}] Régime C - Repos périodiques détectés : "
            f"{repos_summary.total_rp_days} RP au total, "
            f"dont {repos_summary.total_rp_sundays} dimanches. "
            f"Minima annuels attendus : "
            f"{self.MIN_RP_ANNUELS} RP / {self.MIN_RP_DIMANCHES} dimanches."
        )
        alerts.append(
            self.info(
                msg=summary_msg,
                code="REGIME_C_REPOS_SYNTHESIS",
            )
        )

        # 3) Si année incomplète → pas de contrôle bloquant
        if not is_full:
            info_msg = (
                f"[{year}] Période incomplète : les minima annuels pour le régime C "
                "ne sont pas contrôlés de manière stricte sur une portion d'année."
            )
            alerts.append(
                self.info(
                    msg=info_msg,
                    code="REGIME_C_REPOS_PARTIAL_YEAR",
                )
            )
            return True, alerts

        # 4) Année civile complète → contrôles stricts
        if repos_summary.total_rp_days < self.MIN_RP_ANNUELS:
            alerts.append(
                self.error(
                    msg=(
                        f"[{year}] Repos périodiques insuffisants pour le régime C : "
                        f"{repos_summary.total_rp_days}/{self.MIN_RP_ANNUELS} jours sur l'année."
                    ),
                    code="REGIME_C_REPOS_RP_INSUFFISANTS",
                )
            )

        if repos_summary.total_rp_sundays < self.MIN_RP_DIMANCHES:
            alerts.append(
                self.error(
                    msg=(
                        f"[{year}] Dimanches de repos insuffisants pour le régime C : "
                        f"{repos_summary.total_rp_sundays}/{self.MIN_RP_DIMANCHES} dimanches sur l'année."
                    ),
                    code="REGIME_C_REPOS_DIMANCHES_INSUFFISANTS",
                )
            )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
