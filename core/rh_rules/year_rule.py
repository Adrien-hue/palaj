from abc import ABC, abstractmethod
from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity

class YearRule(BaseRule, ABC):
    """
    Règle appliquée à l'échelle de l'année civile (01/01 → 31/12).

    Pour chaque année couverte par le contexte, on appelle :
      check_year(context, year, year_start, year_end, is_full)
    """

    scope = RuleScope.PERIOD

    @abstractmethod
    def check_year(
        self,
        context: PlanningContext,
        year: int,
        year_start: date,
        year_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        """
        Implémentation métier pour une année.

        is_full = True  → l'année est complètement couverte (du 1/1 au 31/12)
        is_full = False → l'année est partiellement couverte.
        """
        raise NotImplementedError

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        if not context.start_date or not context.end_date:
            return False, [
                self.error(
                    "Impossible de déterminer les dates de début/fin pour l'analyse annuelle.",
                    code="YEAR_DATES_MISSING",
                )
            ]

        ctx_start = context.start_date
        ctx_end = context.end_date

        if not context.work_days:
            # Pas de jours → rien à analyser
            return True, []

        is_valid_global = True

        # On gère potentiellement plusieurs années
        for year in range(ctx_start.year, ctx_end.year + 1):
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)

            # Intersection contexte ↔ année
            overlap_start = max(ctx_start, year_start)
            overlap_end = min(ctx_end, year_end)

            # Aucun recouvrement avec cette année → on ignore
            if overlap_start > overlap_end:
                continue

            # Sous-ensemble des WorkDay pour cette année-là (dans l’overlap)
            wd_year = [
                wd
                for wd in context.work_days
                if overlap_start <= wd.jour <= overlap_end
            ]

            # Année "complète" si le contexte couvre toute l'année civile
            is_full = (ctx_start <= year_start) and (ctx_end >= year_end)

            ok, year_alerts = self.check_year(
                context=context,
                year=year,
                year_start=year_start,
                year_end=year_end,
                is_full=is_full,
                work_days=wd_year,
            )

            is_valid_global = is_valid_global and ok
            alerts.extend(year_alerts)

        return is_valid_global, alerts