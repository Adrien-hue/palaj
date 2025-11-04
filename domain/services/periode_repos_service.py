# core/domain/services/periode_repos_service.py
from datetime import date, timedelta
from typing import List

from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities.periode_repos import PeriodeRepos
from core.domain.entities import TypeJour

class PeriodeReposService:
    """Détection des périodes de repos effectif à partir des WorkDays."""

    def detect_periodes_repos(self, context: PlanningContext) -> List[PeriodeRepos]:
        repos_days = sorted(
            [wd.jour for wd in context.work_days if wd.type() == TypeJour.REPOS]
        )

        if not repos_days:
            return []

        periodes: List[PeriodeRepos] = []
        bloc = [repos_days[0]]

        for i in range(1, len(repos_days)):
            prev, curr = repos_days[i - 1], repos_days[i]
            if (curr - prev).days == 1:
                bloc.append(curr)
            else:
                periodes.append(PeriodeRepos(start=bloc[0], end=bloc[-1], jours=bloc))
                bloc = [curr]

        if bloc:
            periodes.append(PeriodeRepos(start=bloc[0], end=bloc[-1], jours=bloc))

        return periodes
