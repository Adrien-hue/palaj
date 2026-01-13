from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.analyzers.rest_stats_analyzer import RestStatsAnalyzer
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.year_rule import YearRule


class ReposAnnuelRule(YearRule):
    """
    Annual rest rule:
    - Count rest periods (1/2/3/4+ days)
    - Count RPSD (Sat->Sun) and WERP (Sat->Sun or Sun->Mon)

    Full year: enforce minima (ERROR)
    Partial year: INFO only
    """

    name = "ReposAnnuelRule"
    description = "Analyse annuelle des repos (RP, RP double, RPSD, WERP)."

    MIN_RP_DOUBLE = 52
    MIN_WERP = 14
    MIN_RPSD = 12

    def __init__(self, analyzer: RestStatsAnalyzer | None = None) -> None:
        self.analyzer = analyzer or RestStatsAnalyzer()

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

        repos_summary = self.analyzer.summarize_rh_days(days)

        # No rest periods -> no noise in engine
        if not repos_summary.periods:
            return RuleResult.ok()

        # Partial year -> no strict checks (no noise)
        if not is_full:
            return RuleResult.ok()

        violations: List[RhViolation] = []

        rp_double = repos_summary.rp_double
        rp_triple = repos_summary.rp_triple
        rp_4plus = repos_summary.rp_4plus
        rpsd = repos_summary.rpsd
        werp = repos_summary.werp

        total_double_equiv = rp_double + rp_triple + rp_4plus

        if total_double_equiv < self.MIN_RP_DOUBLE:
            violations.append(
                self.error_v(
                    code="REPOS_ANNUEL_RP_DOUBLE_INSUFFISANT",
                    msg=(
                        f"[{year}] Repos doubles insuffisants : "
                        f"{total_double_equiv}/{self.MIN_RP_DOUBLE} "
                        f"(dont {rp_triple} triples, {rp_4plus} de 4+ jours)."
                    ),
                    start_date=year_start,
                    end_date=year_end,
                    meta={
                        "year": year,
                        "double_equiv": total_double_equiv,
                        "min_required": self.MIN_RP_DOUBLE,
                        "rp_double": rp_double,
                        "rp_triple": rp_triple,
                        "rp_4plus": rp_4plus,
                    },
                )
            )

        if werp < self.MIN_WERP:
            violations.append(
                self.error_v(
                    code="REPOS_ANNUEL_WERP_INSUFFISANT",
                    msg=f"[{year}] WERP insuffisants : {werp}/{self.MIN_WERP}.",
                    start_date=year_start,
                    end_date=year_end,
                    meta={"year": year, "werp": werp, "min_required": self.MIN_WERP},
                )
            )

        if rpsd < self.MIN_RPSD:
            violations.append(
                self.error_v(
                    code="REPOS_ANNUEL_RPSD_INSUFFISANT",
                    msg=f"[{year}] RPSD insuffisants : {rpsd}/{self.MIN_RPSD}.",
                    start_date=year_start,
                    end_date=year_end,
                    meta={"year": year, "rpsd": rpsd, "min_required": self.MIN_RPSD},
                )
            )

        return RuleResult(violations=violations)
