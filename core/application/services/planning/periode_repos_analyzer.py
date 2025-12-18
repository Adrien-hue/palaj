# core/application/services/planning/periode_repos_analyzer.py
from typing import List

from core.domain.contexts.planning_context import PlanningContext
from core.domain.models.periode_repos import PeriodeRepos
from core.domain.models.work_day import WorkDay
from core.domain.entities import TypeJour


class PeriodeReposAnalyzer:
    """
    Analyse des WorkDay et extraction de toutes les périodes de repos consécutifs.

    Un repos = TypeJour.REPOS uniquement.

    API principale :
        - detect_from_workdays(work_days: List[WorkDay]) -> List[PeriodeRepos]

    API legacy (pour compatibilité) :
        - detect(context: PlanningContext) -> List[PeriodeRepos]
          qui délègue simplement à detect_from_workdays(context.work_days)
    """

    def detect_from_workdays(self, work_days: List[WorkDay]) -> List[PeriodeRepos]:
        """
        Détecte les périodes de repos consécutifs à partir d'une liste de WorkDay.

        - On considère qu'un jour est "repos" si wd.type() == TypeJour.REPOS.
        - On groupe les repos consécutifs (dans l'ordre chronologique des WorkDay).
        """
        if not work_days:
            return []

        repos_periods: List[PeriodeRepos] = []
        current_block: List[WorkDay] = []

        # On trie les jours (sécurité)
        sorted_days = sorted(work_days, key=lambda wd: wd.jour)

        for wd in sorted_days:
            if wd.type() == TypeJour.REPOS:
                # ajout au bloc courant
                current_block.append(wd)
            else:
                # On ferme un bloc si présent
                if current_block:
                    repos_periods.append(
                        PeriodeRepos.from_days([d.jour for d in current_block])
                    )
                    current_block = []

        # Fin de boucle → fermer le dernier bloc
        if current_block:
            repos_periods.append(
                PeriodeRepos.from_days([d.jour for d in current_block])
            )

        return repos_periods

    def detect(self, context: PlanningContext) -> List[PeriodeRepos]:
        """
        Méthode historique : détecte les périodes de repos à partir d'un PlanningContext.

        Délègue simplement à detect_from_workdays pour ne pas dupliquer la logique.
        """
        if not context.work_days:
            return []

        return self.detect_from_workdays(context.work_days)
