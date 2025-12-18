from abc import ABC, abstractmethod
from calendar import monthrange
from datetime import date
from typing import Iterable, List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert, Severity


class MonthRule(BaseRule, ABC):
    """
    Règle appliquée sur des mois civils.

    - Découpe la période du contexte en (année, mois)
    - Pour chaque mois :
        * calcule l'intersection avec le contexte
        * construit la liste des WorkDay du mois (dans l'overlap)
        * détermine si le mois est complètement couvert par le contexte
        * appelle check_month(...) avec ces informations

    Les sous-classes n'ont plus à gérer la boucle ni le filtrage par mois.
    """

    scope = RuleScope.PERIOD

    @abstractmethod
    def check_month(
        self,
        context: PlanningContext,
        year: int,
        month: int,
        month_start: date,
        month_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        """
        Implémentation métier pour un mois donné.

        is_full = True  →  le contexte couvre tout le mois civil (1er → dernier jour)
        is_full = False →  mois partiellement couvert (on fait souvent du suivi/INFO).
        """
        raise NotImplementedError

    def _iter_months_in_context(self, start: date, end: date) -> Iterable[tuple[int, int]]:
        """Génère tous les couples (year, month) entre start et end inclus."""
        year, month = start.year, start.month
        while (year, month) <= (end.year, end.month):
            yield year, month
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        start, end = context.start_date, context.end_date
        if not start or not end:
            return False, [
                self.error(
                    "Impossible de déterminer les bornes de la période pour une règle mensuelle.",
                    code="MONTH_NO_DATES",
                )
            ]

        if not context.work_days:
            # rien à analyser
            return True, []

        alerts: List[DomainAlert] = []
        is_valid_global = True

        for year, month in self._iter_months_in_context(start, end):
            month_start = date(year, month, 1)
            month_end = date(year, month, monthrange(year, month)[1])

            # Intersection contexte ↔ mois
            overlap_start = max(start, month_start)
            overlap_end = min(end, month_end)

            # Aucun recouvrement → on ignore ce mois
            if overlap_start > overlap_end:
                continue

            # Sous-ensemble de WorkDay pour ce mois (dans l’overlap)
            wd_month = [
                wd
                for wd in context.work_days
                if overlap_start <= wd.jour <= overlap_end
            ]

            # Mois "complet" si le contexte couvre tout le mois civil
            is_full = (start <= month_start) and (end >= month_end)

            ok, month_alerts = self.check_month(
                context=context,
                year=year,
                month=month,
                month_start=month_start,
                month_end=month_end,
                is_full=is_full,
                work_days=wd_month,
            )

            is_valid_global = is_valid_global and ok
            alerts.extend(month_alerts)

        is_valid_global = is_valid_global and all(a.severity != Severity.ERROR for a in alerts)
        return is_valid_global, alerts
