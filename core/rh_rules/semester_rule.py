# core/rh_rules/semester_rule.py
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import List

from core.rh_rules.base_rule import BaseRule
from core.rh_rules.contexts import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_violation import RhViolation
from core.rh_rules.models.rule_result import RuleResult
from core.rh_rules.models.rule_scope import RuleScope


class SemesterRule(BaseRule, ABC):
    """
    PERIOD rule split by civil semesters (RH-first):
      - S1: 01/01 -> 30/06
      - S2: 01/07 -> 31/12
    """

    scope = RuleScope.PERIOD

    @abstractmethod
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
        raise NotImplementedError

    def _semester_ranges_for_year(self, year: int) -> list[tuple[str, date, date]]:
        return [
            ("S1", date(year, 1, 1), date(year, 6, 30)),
            ("S2", date(year, 7, 1), date(year, 12, 31)),
        ]

    def check(self, context: RhContext) -> RuleResult:
        start = context.effective_start
        end = context.effective_end

        if not start or not end:
            v = self.error_v(
                code="SEMESTER_DATES_MISSING",
                msg="Impossible de déterminer les dates de début/fin pour l'analyse semestrielle.",
                start_date=context.start_date,
                end_date=context.end_date,
                meta={
                    "window_start": str(context.window_start) if context.window_start else None,
                    "window_end": str(context.window_end) if context.window_end else None,
                },
            )
            return RuleResult(violations=[v])

        if not context.days:
            return RuleResult(violations=[])

        violations: list[RhViolation] = []

        for year in range(start.year, end.year + 1):
            for label, sem_start, sem_end in self._semester_ranges_for_year(year):
                overlap_start = max(start, sem_start)
                overlap_end = min(end, sem_end)
                if overlap_start > overlap_end:
                    continue

                days_sem = [d for d in context.days if overlap_start <= d.day_date <= overlap_end]
                is_full = (start <= sem_start) and (end >= sem_end)

                result = self.check_semester(
                    context=context,
                    year=year,
                    label=label,
                    sem_start=sem_start,
                    sem_end=sem_end,
                    is_full=is_full,
                    days=days_sem,
                )
                violations.extend(result.violations)

        return RuleResult(violations=violations)