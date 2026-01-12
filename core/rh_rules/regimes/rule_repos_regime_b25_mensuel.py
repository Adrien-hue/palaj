# core/rh_rules/regimes/rule_repos_regime_b25_mensuel.py
from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.month_rule import MonthRule


class RegimeB25ReposMensuelRule(MonthRule):
    """
    Regime B25 (regime_id = 1)

    For each FULL civil month:
      - At least 1 RPSD (Saturday->Sunday rest period)
      - At least 2 rest periods of >= 2 days total (including >=1 RPSD)

    Partial month:
      - no blocking controls (silent)
    """

    name = "RegimeB25ReposMensuelRule"
    description = (
        "Contrôle mensuel des repos B25 : par mois complet, au moins 1 RPSD et "
        "au moins 2 périodes de repos de 2+ jours (dont ≥1 RPSD)."
    )

    MIN_RPSD = 1
    MIN_RP_2PLUS = 2

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

    def applies_to(self, context: RhContext) -> bool:
        return getattr(context.agent, "regime_id", None) == 1

    def check(self, context: RhContext) -> RuleResult:
        if not self.applies_to(context):
            return RuleResult.ok()
        return super().check(context)

    def check_month(
        self,
        context: RhContext,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        days: List[RhDay],
    ) -> RuleResult:
        # No data for this month slice -> neutral
        if not days:
            return RuleResult.ok()

        # Partial month -> silent (no enforcement)
        if not is_full:
            return RuleResult.ok()

        # Compute rest stats on the slice days
        summary = self.analyzer.summarize_rh_days(days)

        rpsd_count = 0
        rp_2plus_count = 0

        # IMPORTANT:
        # - MonthRule already slices "days" within [month_start..month_end].
        # - A RestPeriod may theoretically start before month_start if the month is full
        #   but context is larger; however the slice prevents that, so "start in window"
        #   should always hold. We keep a safe guard anyway.
        for p in summary.periods:
            if not (month_start <= p.start <= month_end):
                continue
            if p.nb_jours >= 2:
                rp_2plus_count += 1
            if p.is_rpsd():
                rpsd_count += 1

        if rpsd_count >= self.MIN_RPSD and rp_2plus_count >= self.MIN_RP_2PLUS:
            return RuleResult.ok()

        label = f"{year}-{month:02d}"
        violations: List[RhViolation] = []

        violations.append(
            self.error_v(
                code="B25_MOIS_NON_CONFORME",
                msg=(
                    f"[{label}] Régime B25 - Repos mensuels insuffisants : "
                    f"RPSD={rpsd_count} (min {self.MIN_RPSD}), "
                    f"RP doubles/2+={rp_2plus_count} (min {self.MIN_RP_2PLUS})."
                ),
                start_date=month_start,
                end_date=month_end,
                meta={
                    "year": year,
                    "month": month,
                    "label": label,
                    "regime_id": 1,
                    "is_full": is_full,
                    "rpsd": rpsd_count,
                    "rp_2plus": rp_2plus_count,
                    "min_rpsd": self.MIN_RPSD,
                    "min_rp_2plus": self.MIN_RP_2PLUS,
                    "total_rest_days": summary.total_rest_days,
                    "total_rest_sundays": summary.total_rest_sundays,
                },
            )
        )

        return RuleResult(violations=violations)
