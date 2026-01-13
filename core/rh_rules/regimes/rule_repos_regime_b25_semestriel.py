# core/rh_rules/regimes/rule_repos_regime_b25_semestriel.py
from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.semester_rule import SemesterRule


class RegimeB25ReposSemestrielRule(SemesterRule):
    """
    Regime B25 (regime_id = 1)

    For each FULL civil semester:
      - At least 56 periodic rest days (RP) per semester:
        - S1: 01/01 -> 30/06
        - S2: 01/07 -> 31/12

    Partial semester:
      - no blocking controls (silent)
    """

    name = "RegimeB25ReposSemestrielRule"
    description = "Repos semestriels spécifiques au régime B25 (≥ 56 RP par semestre)."

    MIN_RP_SEMESTRE = 56

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    def applies_to(self, context: RhContext) -> bool:
        return getattr(context.agent, "regime_id", None) == 1

    def check(self, context: RhContext) -> RuleResult:
        if not self.applies_to(context):
            return RuleResult.ok()
        return super().check(context)

    def check_semester(
        self,
        context: RhContext,
        year: int,
        label: str,  # "S1" or "S2"
        sem_start: date,
        sem_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        # No data -> neutral
        if not days:
            return RuleResult.ok()

        # Partial semester -> silent (no enforcement)
        if not is_full:
            return RuleResult.ok()

        summary = self.analyzer.summarize_rh_days(days)
        nb_rp_sem = summary.total_rest_days

        if nb_rp_sem >= self.MIN_RP_SEMESTRE:
            return RuleResult.ok()

        v: RhViolation = self.error_v(
            code="B25_SEMESTRE_RP_INSUFFISANTS",
            msg=(
                f"[{year} {label}] Repos périodiques insuffisants pour le régime B25 "
                f"sur le semestre {sem_start} → {sem_end} : "
                f"{nb_rp_sem}/{self.MIN_RP_SEMESTRE} jours."
            ),
            start_date=sem_start,
            end_date=sem_end,
            meta={
                "year": year,
                "label": label,
                "regime_id": 1,
                "is_full": is_full,
                "total_rest_days": nb_rp_sem,
                "min_required": self.MIN_RP_SEMESTRE,
                "total_rest_sundays": summary.total_rest_sundays,
            },
        )
        return RuleResult(violations=[v])
