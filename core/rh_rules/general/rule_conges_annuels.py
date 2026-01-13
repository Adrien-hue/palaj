from __future__ import annotations

from datetime import date
from typing import List

from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.year_rule import YearRule

from core.domain.enums.day_type import DayType
from core.rh_rules.analyzers.leave_period_analyzer import LeavePeriodAnalyzer


class CongesAnnuelRule(YearRule):
    """
    Annual leave rule:
    - 28 annual leave days (DayType.LEAVE)
    - at least one leave block (leave + rest) of 15 consecutive days
    """

    name = "CongesAnnuelRule"
    description = "Contrôle annuel des congés (quotas et périodes longues)."

    MIN_CONGES_ANNUELS = 28
    MIN_CONGE_BLOCK = 15

    def __init__(self, analyzer: LeavePeriodAnalyzer | None = None) -> None:
        self.analyzer = analyzer or LeavePeriodAnalyzer()

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

        periodes = self.analyzer.detect_from_rh_days(days)

        total_leave = sum(1 for d in days if d.day_type == DayType.LEAVE)

        nb_blocks_15_plus = sum(1 for p in periodes if p.nb_jours >= self.MIN_CONGE_BLOCK)
        longest_block = max((p.nb_jours for p in periodes), default=0)

        violations: List[RhViolation] = []

        if is_full:
            if total_leave < self.MIN_CONGES_ANNUELS:
                violations.append(
                    self.error_v(
                        code="CONGES_ANNUELS_QUOTA_INSUFFISANT",
                        msg=f"[{year}] Nombre de congés annuels insuffisant : {total_leave}/{self.MIN_CONGES_ANNUELS}.",
                        start_date=year_start,
                        end_date=year_end,
                        meta={"year": year, "leave_days": total_leave, "min_required": self.MIN_CONGES_ANNUELS},
                    )
                )

            if nb_blocks_15_plus == 0:
                violations.append(
                    self.error_v(
                        code="CONGES_ANNUELS_BLOC_LONG_MANQUANT",
                        msg=(
                            f"[{year}] Aucune période de congés consécutifs "
                            f"(congé + repos) de {self.MIN_CONGE_BLOCK} jours ou plus détectée."
                        ),
                        start_date=year_start,
                        end_date=year_end,
                        meta={"year": year, "min_block_days": self.MIN_CONGE_BLOCK, "longest_block_days": longest_block},
                    )
                )

        return RuleResult(violations=violations)
