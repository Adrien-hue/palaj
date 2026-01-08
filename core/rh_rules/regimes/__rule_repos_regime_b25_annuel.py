# core/rh_rules/rule_repos_regime_b25_annuel.py
from __future__ import annotations

from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.year_rule import YearRule
from core.utils.domain_alert import DomainAlert, Severity
from core.application.services.planning.repos_stats_analyzer import ReposStatsAnalyzer


class RegimeB25ReposAnnuelRule(YearRule):
    """
    Règle annuelle spécifique au régime B25 (regime_id = 1).

    Exigences (par année civile complète) :
    - Au moins 114 jours de repos périodiques (RP)
    - Dont au moins 30 dimanches de repos
    """

    name = "RegimeB25ReposAnnuelRule"
    description = "Repos annuels spécifiques au régime B25 (114 RP / 30 dimanches)."

    MIN_RP_ANNUELS = 114
    MIN_RP_DIMANCHES = 30

    def __init__(self, analyzer: ReposStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or ReposStatsAnalyzer()

    # ---------------------------------------------------------
    # Applicabilité de la règle
    # ---------------------------------------------------------
    def applies_to(self, context: PlanningContext) -> bool:
        """
        La règle ne s'applique qu'aux agents de régime B25 (regime_id = 1).
        """
        regime_id = getattr(context.agent, "regime_id", None)
        return regime_id == 1

    # On surcharge check pour ignorer les agents hors B25,
    # puis laisser YearRule gérer le découpage par année.
    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        if not self.applies_to(context):
            return True, []
        return super().check(context)

    # ---------------------------------------------------------
    # Implémentation annuelle (par année civile)
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

        # Aucun jour pour cette année → simple info
        if not work_days:
            alerts.append(
                self.info(
                    msg=f"[{year}] Régime B25 : aucun jour planifié dans cette année.",
                    code="B25_ANNUEL_ANNEE_VIDE",
                )
            )
            return True, alerts

        # Statistiques de repos pour CETTE année (sur les work_days filtrés de l'année)
        repos_summary = self.analyzer.summarize_workdays(work_days)

        # Résumé informatif systématique
        alerts.append(
            self.info(
                msg=(
                    f"[{year}] Régime B25 - Repos périodiques détectés : "
                    f"{repos_summary.total_rp_days} jours de repos, "
                    f"dont {repos_summary.total_rp_sundays} dimanches. "
                    f"Minima attendus : {self.MIN_RP_ANNUELS} RP / "
                    f"{self.MIN_RP_DIMANCHES} dimanches."
                ),
                code="B25_ANNUEL_SYNTHESIS",
            )
        )

        # Année incomplète → pas de contrôle bloquant, info uniquement
        if not is_full:
            alerts.append(
                self.info(
                    msg=(
                        f"[{year}] Période incomplète : les minima annuels B25 "
                        "(114 RP / 30 dimanches) ne sont pas contrôlés strictement."
                    ),
                    code="B25_ANNUEL_PERIODE_PARTIELLE",
                )
            )
            return True, alerts

        # Année civile complète → contrôles stricts
        if repos_summary.total_rp_days < self.MIN_RP_ANNUELS:
            alerts.append(
                self.error(
                    msg=(
                        f"[{year}] Repos périodiques insuffisants pour le régime B25 : "
                        f"{repos_summary.total_rp_days}/{self.MIN_RP_ANNUELS} jours sur l'année."
                    ),
                    code="B25_ANNUEL_RP_INSUFFISANTS",
                )
            )

        if repos_summary.total_rp_sundays < self.MIN_RP_DIMANCHES:
            alerts.append(
                self.error(
                    msg=(
                        f"[{year}] Dimanches de repos insuffisants pour le régime B25 : "
                        f"{repos_summary.total_rp_sundays}/{self.MIN_RP_DIMANCHES} dimanches sur l'année."
                    ),
                    code="B25_ANNUEL_DIMANCHES_INSUFFISANTS",
                )
            )

        is_valid = all(a.severity != Severity.ERROR for a in alerts)
        return is_valid, alerts
