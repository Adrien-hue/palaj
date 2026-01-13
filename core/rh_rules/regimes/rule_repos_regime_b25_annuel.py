# core/rh_rules/regimes/rule_repos_regime_b25_annuel.py
from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.year_rule import YearRule


class RegimeB25ReposAnnuelRule(YearRule):
    """
    Regime B25 (regime_id = 1)

    Full civil year requirements:
    - At least 114 periodic rest days (RP)
    - Including at least 30 Sundays of rest

    Partial year:
    - no blocking controls
    """

    name = "RegimeB25ReposAnnuelRule"
    description = "Repos annuels spécifiques au régime B25 (114 RP / 30 dimanches)."

    MIN_RP_ANNUELS = 114
    MIN_RP_DIMANCHES = 30

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    # ---------------------------------------------------------
    # Applicability
    # ---------------------------------------------------------
    def applies_to(self, context: RhContext) -> bool:
        return getattr(context.agent, "regime_id", None) == 1

    def check(self, context: RhContext) -> RuleResult:
        if not self.applies_to(context):
            return RuleResult.ok()
        return super().check(context)

    # ---------------------------------------------------------
    # Year logic
    # ---------------------------------------------------------
    def check_year(
        self,
        context: RhContext,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        # No data for this year
        if not days:
            return RuleResult.ok()

        # Partial year: no blocking controls (silent for now)
        if not is_full:
            return RuleResult.ok()

        repos_summary = self.analyzer.summarize_rh_days(days)

        total_rest_days = repos_summary.total_rest_days
        total_rest_sundays = repos_summary.total_rest_sundays

        violations: List[RhViolation] = []

        if total_rest_days < self.MIN_RP_ANNUELS:
            violations.append(
                self.error_v(
                    code="B25_ANNUEL_RP_INSUFFISANTS",
                    msg=(
                        f"[{year}] Repos périodiques insuffisants pour le régime B25 : "
                        f"{total_rest_days}/{self.MIN_RP_ANNUELS} jours sur l'année."
                    ),
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "regime_id": 1,
                        "total_rest_days": total_rest_days,
                        "min_required": self.MIN_RP_ANNUELS,
                    },
                )
            )

        if total_rest_sundays < self.MIN_RP_DIMANCHES:
            violations.append(
                self.error_v(
                    code="B25_ANNUEL_DIMANCHES_INSUFFISANTS",
                    msg=(
                        f"[{year}] Dimanches de repos insuffisants pour le régime B25 : "
                        f"{total_rest_sundays}/{self.MIN_RP_DIMANCHES} dimanches sur l'année."
                    ),
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "regime_id": 1,
                        "total_rest_sundays": total_rest_sundays,
                        "min_required": self.MIN_RP_DIMANCHES,
                    },
                )
            )

        return RuleResult(violations=violations)
