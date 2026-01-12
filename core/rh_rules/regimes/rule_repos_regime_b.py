from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.year_rule import YearRule


class RegimeBReposRule(YearRule):
    """
    Regime B (regime_id = 0)

    Full civil year requirements:
    - At least 114 periodic rest days (RP)
    - Including at least 52 Sundays of rest

    Partial year:
    - no blocking controls
    """

    name = "RegimeBReposRule"
    description = "Repos annuels spécifiques au régime B (114 RP / 52 dimanches)."

    MIN_RP_ANNUELS = 114
    MIN_RP_DIMANCHES = 52

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    def applies_to(self, context: RhContext) -> bool:
        return getattr(context.agent, "regime_id", None) == 0

    def check(self, context: RhContext) -> RuleResult:
        if not self.applies_to(context):
            return RuleResult.ok()
        return super().check(context)

    def check_year(
        self,
        context: RhContext,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        if not days:
            return RuleResult.ok()

        # Partial year => no blocking controls (silent OK for now)
        if not is_full:
            return RuleResult.ok()

        repos_summary = self.analyzer.summarize_rh_days(days)

        violations: List[RhViolation] = []

        total_rest_days = repos_summary.total_rest_days
        total_rest_sundays = repos_summary.total_rest_sundays

        if total_rest_days < self.MIN_RP_ANNUELS:
            violations.append(
                self.error_v(
                    code="REGIME_B_REPOS_RP_INSUFFISANTS",
                    msg=(
                        f"[{year}] Repos périodiques insuffisants pour le régime B : "
                        f"{total_rest_days}/{self.MIN_RP_ANNUELS} jours sur l'année."
                    ),
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "regime_id": 0,
                        "total_rest_days": total_rest_days,
                        "min_required": self.MIN_RP_ANNUELS,
                    },
                )
            )

        if total_rest_sundays < self.MIN_RP_DIMANCHES:
            violations.append(
                self.error_v(
                    code="REGIME_B_REPOS_DIMANCHES_INSUFFISANTS",
                    msg=(
                        f"[{year}] Dimanches de repos insuffisants pour le régime B : "
                        f"{total_rest_sundays}/{self.MIN_RP_DIMANCHES} dimanches sur l'année."
                    ),
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "regime_id": 0,
                        "total_rest_sundays": total_rest_sundays,
                        "min_required": self.MIN_RP_DIMANCHES,
                    },
                )
            )

        return RuleResult(violations=violations)
