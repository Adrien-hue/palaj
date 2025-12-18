from abc import ABC, abstractmethod
from datetime import date
from typing import List, Tuple

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.work_day import WorkDay
from core.rh_rules.base_rule import BaseRule, RuleScope
from core.utils.domain_alert import DomainAlert


class SemesterRule(BaseRule, ABC):
    """
    Règle appliquée sur les semestres civils :

    - S1 : 01/01 → 30/06
    - S2 : 01/07 → 31/12

    Pour chaque année couverte par le contexte, on appelle :
      check_semester(context, year, label, sem_start, sem_end, is_full, work_days)
    """

    scope = RuleScope.PERIOD

    @abstractmethod
    def check_semester(
        self,
        context: PlanningContext,
        year: int,
        label: str,  # "S1" ou "S2"
        sem_start: date,
        sem_end: date,
        is_full: bool,
        work_days: List[WorkDay],
    ) -> Tuple[bool, List[DomainAlert]]:
        """
        Implémentation métier pour un semestre.

        is_full = True  → le semestre est entièrement couvert par le contexte
        is_full = False → le semestre n'est que partiellement couvert.
        """
        raise NotImplementedError

    def _semester_ranges_for_year(self, year: int) -> list[tuple[str, date, date]]:
        """Retourne [("S1", start, end), ("S2", start, end)] pour l'année donnée."""
        return [
            ("S1", date(year, 1, 1), date(year, 6, 30)),
            ("S2", date(year, 7, 1), date(year, 12, 31)),
        ]

    def check(self, context: PlanningContext) -> Tuple[bool, List[DomainAlert]]:
        alerts: List[DomainAlert] = []

        if not context.start_date or not context.end_date:
            return False, [
                self.error(
                    "Impossible de déterminer les dates de début/fin pour l'analyse semestrielle.",
                    code="SEMESTER_DATES_MISSING",
                )
            ]

        ctx_start = context.start_date
        ctx_end = context.end_date

        if not context.work_days:
            # Contexte vide : rien à analyser
            return True, []

        is_valid_global = True

        # On gère potentiellement plusieurs années si le contexte les couvre
        for year in range(ctx_start.year, ctx_end.year + 1):
            for label, sem_start, sem_end in self._semester_ranges_for_year(year):
                # Intersection contexte ↔ semestre
                overlap_start = max(ctx_start, sem_start)
                overlap_end = min(ctx_end, sem_end)

                # Aucun recouvrement → on ignore ce semestre
                if overlap_start > overlap_end:
                    continue

                # Sous-ensemble de WorkDay pour ce semestre uniquement
                wd_semester = [
                    wd
                    for wd in context.work_days
                    if overlap_start <= wd.jour <= overlap_end
                ]

                # On considère que le semestre est "complet" si le contexte
                # couvre tout le semestre civil (peu importe qu'il y ait du travail ou pas)
                is_full = (ctx_start <= sem_start) and (ctx_end >= sem_end)

                ok, sem_alerts = self.check_semester(
                    context=context,
                    year=year,
                    label=label,
                    sem_start=sem_start,
                    sem_end=sem_end,
                    is_full=is_full,
                    work_days=wd_semester,
                )

                is_valid_global = is_valid_global and ok
                alerts.extend(sem_alerts)

        return is_valid_global, alerts
