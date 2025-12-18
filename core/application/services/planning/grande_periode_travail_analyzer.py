# core/application/services/planning/grande_periode_travail_analyzer.py

from datetime import date
from typing import List

from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour
from core.domain.models.grande_periode_travail import GrandePeriodeTravail
from core.domain.models.work_day import WorkDay


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
