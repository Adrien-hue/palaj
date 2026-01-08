# core/application/services/planning/grande_periode_travail_analyzer.py

from datetime import date
from typing import List, Optional

from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour
from core.domain.models.grande_periode_travail import GrandePeriodeTravail
from core.domain.models.work_day import WorkDay

from core.domain.enums.day_type import DayType
from core.rh_rules.models.gpt_block import GptBlock
from core.rh_rules.models.rh_day import RhDay


class GrandePeriodeTravailAnalyzer:
    """Service de détection et d'analyse des Grandes Périodes de Travail (GPT)."""

    # =====================================================================
    # PUBLIC API 1 : API moderne → fonctionne directement sur work_days
    # =====================================================================
    def detect_from_workdays(
        self,
        work_days: List[WorkDay],
        *,
        context_start: None | date = None,
        context_end: None | date = None,
    ) -> List[GrandePeriodeTravail]:
        """
        Détecte les Grandes Périodes de Travail (GPT) dans une liste triée
        ou non de WorkDay.

        - POSTE / ZCOT / ABSENCE / CONGE → inclus dans une GPT
        - REPOS → coupe une GPT
        - Les GPT en début/fin peuvent être marquées comme tronquées si les
          bornes contextuelles sont fournies.
        """

        if not work_days:
            return []

        work_days_sorted = sorted(work_days, key=lambda wd: wd.jour)
        gpts: List[GrandePeriodeTravail] = []
        bloc: List[WorkDay] = []

        for i, wd in enumerate(work_days_sorted):
            t = wd.type()

            if t == TypeJour.REPOS:
                # Fin d'une GPT
                if bloc:
                    gpt = self._finalize_gpt(
                        bloc,
                        context_start=context_start,
                        context_end=context_end,
                    )
                    if gpt:
                        gpts.append(gpt)
                    bloc = []
            else:
                # Tous les jours non repos sont intégrés dans une GPT
                bloc.append(wd)

                # Fin du tableau → clôture
                if i == len(work_days_sorted) - 1:
                    gpt = self._finalize_gpt(
                        bloc,
                        context_start=context_start,
                        context_end=context_end,
                    )
                    if gpt:
                        gpts.append(gpt)

        return gpts

    # =====================================================================
    # PUBLIC API 2 : backward compatibility → fonctionne avec PlanningContext
    # =====================================================================
    def detect(self, context: PlanningContext) -> List[GrandePeriodeTravail]:
        """
        API legacy : conserve l'ancien usage.
        Délègue à detect_from_workdays().
        """
        if not context.work_days:
            return []

        return self.detect_from_workdays(
            context.work_days,
            context_start=context.start_date,
            context_end=context.end_date,
        )
    
    def detect_from_rh_days(
        self,
        days: List[RhDay],
        window_start: Optional[date] = None,
        window_end: Optional[date] = None,
    ) -> List[GptBlock]:
        days_sorted = sorted(days, key=lambda d: d.day_date)

        def is_gpt_work(d: RhDay) -> bool:
            return d.day_type in (DayType.WORKING, DayType.ZCOT)

        gpts: List[GptBlock] = []
        block: List[RhDay] = []

        def close_block():
            nonlocal block
            if not block:
                return
            start = block[0].day_date
            end = block[-1].day_date

            # truncated flags: if the block touches window edges
            left_trunc = bool(window_start and start <= window_start)
            right_trunc = bool(window_end and end >= window_end)

            gpts.append(GptBlock(days=tuple(block), is_left_truncated=left_trunc, is_right_truncated=right_trunc))
            block = []

        for d in days_sorted:
            if is_gpt_work(d):
                if not block:
                    block = [d]
                else:
                    prev = block[-1]
                    if (d.day_date - prev.day_date).days == 1:
                        block.append(d)
                    else:
                        close_block()
                        block = [d]
            else:
                close_block()

        close_block()
        return gpts

    # =====================================================================
    # INTERNAL HELPERS
    # =====================================================================
    def _finalize_gpt(
        self,
        bloc: List[WorkDay],
        *,
        context_start,
        context_end,
    ) -> GrandePeriodeTravail | None:

        if not bloc:
            return None

        start = bloc[0].jour
        end = bloc[-1].jour

        # Une GPT est tronquée si elle déborde du cadre dans lequel on analyse
        is_left_truncated = (
            context_start is not None and start <= context_start
        )

        is_right_truncated = (
            context_end is not None and end >= context_end
        )

        return GrandePeriodeTravail.from_workdays(
            bloc,
            is_left_truncated=is_left_truncated,
            is_right_truncated=is_right_truncated,
        )
