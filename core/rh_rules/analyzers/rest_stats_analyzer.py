from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Set

from core.rh_rules.analyzers.rest_period_analyzer import RestPeriodAnalyzer
from core.rh_rules.models.rest_period import RestPeriod
from core.rh_rules.models.rh_day import RhDay


@dataclass(frozen=True)
class RestSummary:
    """Aggregated stats for REST periods over a set of RH days."""
    periods: List[RestPeriod]

    # Unique rest days
    rest_days: Set[date]

    # Total unique rest days
    total_rest_days: int

    # Total Sundays that are rest days
    total_rest_sundays: int

    # Period counts by length
    rp_simple: int
    rp_double: int
    rp_triple: int
    rp_4plus: int

    # Weekend qualifiers
    rpsd: int  # Sat+Sun
    werp: int  # Sat+Sun OR Sun+Mon


class RestStatsAnalyzer:
    """Computes aggregated statistics from consecutive REST periods."""

    def __init__(self, period_analyzer: RestPeriodAnalyzer | None = None) -> None:
        self.period_analyzer = period_analyzer or RestPeriodAnalyzer()

    def summarize_rh_days(self, rh_days: List[RhDay]) -> RestSummary:
        periods = self.period_analyzer.detect_from_rh_days(rh_days)

        if not periods:
            return RestSummary(
                periods=[],
                rest_days=set(),
                total_rest_days=0,
                total_rest_sundays=0,
                rp_simple=0,
                rp_double=0,
                rp_triple=0,
                rp_4plus=0,
                rpsd=0,
                werp=0,
            )

        rest_days: Set[date] = set()
        total_sundays = 0

        rp_simple = rp_double = rp_triple = rp_4plus = 0
        rpsd = werp = 0

        for pr in periods:
            # Aggregate unique rest days + Sundays count
            for d in pr.days:
                if d not in rest_days:
                    rest_days.add(d)
                    if d.weekday() == 6:  # Sunday
                        total_sundays += 1

            # Period classification
            if pr.is_simple():
                rp_simple += 1
            elif pr.is_double():
                rp_double += 1
            elif pr.is_triple():
                rp_triple += 1
            elif pr.is_4plus():
                rp_4plus += 1

            # Weekend qualifiers
            if pr.is_rpsd():
                rpsd += 1
            if pr.is_werp():
                werp += 1

        return RestSummary(
            periods=periods,
            rest_days=rest_days,
            total_rest_days=len(rest_days),
            total_rest_sundays=total_sundays,
            rp_simple=rp_simple,
            rp_double=rp_double,
            rp_triple=rp_triple,
            rp_4plus=rp_4plus,
            rpsd=rpsd,
            werp=werp,
        )