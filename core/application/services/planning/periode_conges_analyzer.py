# core/application/services/planning/periode_conges_analyzer.py
from __future__ import annotations
from typing import List

from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour
from core.domain.models.work_day import WorkDay
from core.domain.models.periode_conges import PeriodeConges


class PeriodeCongesAnalyzer:
    """
    Service applicatif :

    - detect_from_workdays : détection des périodes de congés à partir
      d'une liste de WorkDay (API générique, indépendante du contexte)
    - detect : compatibilité historique, prend un PlanningContext et
      délègue à detect_from_workdays(context.work_days)

    Règles de détection d'une période de congés :
    - on parcourt les WorkDay triés par date
    - on construit des blocs de jours consécutifs où
      le type est CONGE ou REPOS
    - une période n'est retenue que si le bloc contient
      AU MOINS un jour CONGE
    - un jour de POSTE / ZCOT / ABSENCE casse la période
    """

    def detect_from_workdays(self, work_days: List[WorkDay]) -> List[PeriodeConges]:
        """
        API générique : détecte les périodes de congés à partir d'une
        simple liste de WorkDay (quel que soit le contexte).

        La liste peut couvrir une année, un mois, une période quelconque.
        """
        work_days_sorted = sorted(work_days, key=lambda wd: wd.jour)
        periodes: List[PeriodeConges] = []

        current_block: List[WorkDay] = []
        has_conge = False

        for wd in work_days_sorted:
            t = wd.type()

            if t in (TypeJour.CONGE, TypeJour.REPOS):
                if not current_block:
                    # on démarre un bloc
                    current_block = [wd]
                    has_conge = (t == TypeJour.CONGE)
                else:
                    prev = current_block[-1]
                    # on vérifie la continuité calendaire
                    if (wd.jour - prev.jour).days == 1:
                        current_block.append(wd)
                        if t == TypeJour.CONGE:
                            has_conge = True
                    else:
                        # bloc précédent terminé
                        if has_conge:
                            periodes.append(PeriodeConges.from_workdays(current_block))
                        # on démarre un nouveau bloc
                        current_block = [wd]
                        has_conge = (t == TypeJour.CONGE)
            else:
                # type qui casse le bloc (POSTE, ZCOT, ABSENCE, ...)
                if current_block and has_conge:
                    periodes.append(PeriodeConges.from_workdays(current_block))
                current_block = []
                has_conge = False

        # fin de boucle : on ne doit pas oublier le dernier bloc
        if current_block and has_conge:
            periodes.append(PeriodeConges.from_workdays(current_block))

        return periodes

    def detect(self, context: PlanningContext) -> List[PeriodeConges]:
        """
        Méthode historique : détecte les périodes de congés à partir
        d'un PlanningContext.

        Elle délègue simplement à detect_from_workdays pour ne pas dupliquer
        la logique.
        """
        if not context.work_days:
            return []

        return self.detect_from_workdays(context.work_days)
