# core/application/services/grande_periode_travail_analyzer.py
from datetime import timedelta
from typing import List

from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour
from core.domain.models.grande_periode_travail import GrandePeriodeTravail
from core.domain.models.work_day import WorkDay


class GrandePeriodeTravailAnalyzer:
    """Service de détection et d'analyse des Grandes Périodes de Travail (GPT)."""

    def detect(self, context: PlanningContext) -> List[GrandePeriodeTravail]:
        """
        Détecte les Grandes Périodes de Travail (GPT) à partir des `WorkDay` du contexte.

        Règles :
        - Inclut POSTE et ZCOT (jours travaillés)
        - Inclut aussi ABSENCE / CONGÉ tant qu’il n’y a pas de REPOS entre deux jours travaillés
        - S’arrête uniquement sur REPOS
        - Marque les GPT tronquées si elles débordent du contexte
        """
        if not context.work_days:
            return []

        work_days_sorted = sorted(context.work_days, key=lambda wd: wd.jour)
        gpts: List[GrandePeriodeTravail] = []
        bloc: List[WorkDay] = []

        for i, wd in enumerate(work_days_sorted):
            t = wd.type()

            if t == TypeJour.REPOS:
                # Si repos → clôture de la GPT courante
                if bloc:
                    gpt = self._finalize_gpt(bloc, context)
                    if gpt:
                        gpts.append(gpt)
                    bloc = []
            else:
                # Les jours non-repos (poste, zcot, absence, congé) sont inclus
                bloc.append(wd)

                # Si c’est le dernier jour du planning → on clôture aussi
                if i == len(work_days_sorted) - 1:
                    gpt = self._finalize_gpt(bloc, context)
                    if gpt:
                        gpts.append(gpt)

        return gpts

    # ---------------------------------------------------------
    # 🔧 Helpers internes
    # ---------------------------------------------------------
    def _finalize_gpt(self, bloc: List[WorkDay], context: PlanningContext) -> GrandePeriodeTravail | None:
        """Construit une GPT à partir d’un bloc de WorkDays, en détectant les cas tronqués."""
        if not bloc:
            return None

        start = bloc[0].jour
        end = bloc[-1].jour

        # Une GPT est tronquée si elle déborde du planning analysé
        # Vérifie que les bornes du contexte ne sont pas None avant comparaison
        is_left_truncated = context.start_date is not None and start <= context.start_date
        is_right_truncated = context.end_date is not None and end >= context.end_date

        return GrandePeriodeTravail.from_workdays(
            bloc,
            is_left_truncated=is_left_truncated,
            is_right_truncated=is_right_truncated,
        )
