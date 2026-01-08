# core/application/services/planning/periode_conges_analyzer.py
from __future__ import annotations
from datetime import date
from typing import List

from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour
from core.domain.models.work_day import WorkDay
from core.domain.models.periode_conges import PeriodeConges

from core.domain.enums.day_type import DayType
from core.rh_rules.models.leave_period import LeavePeriod
from core.rh_rules.models.rh_day import RhDay


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
    
    def detect_from_rh_days(self, rh_days: List[RhDay]) -> List[LeavePeriod]:
        if not rh_days:
            return []

        sorted_days = sorted(rh_days, key=lambda d: d.day_date)
        periods: List[LeavePeriod] = []

        block: List[date] = []
        leave_count = 0

        def close():
            nonlocal block, leave_count
            if block and leave_count > 0:
                periods.append(LeavePeriod(days=tuple(block), leave_days=leave_count))
            block = []
            leave_count = 0

        for d in sorted_days:
            t = d.day_type

            if t in (DayType.LEAVE, DayType.REST):
                if not block:
                    block = [d.day_date]
                    leave_count = 1 if t == DayType.LEAVE else 0
                else:
                    if (d.day_date - block[-1]).days == 1:
                        block.append(d.day_date)
                        if t == DayType.LEAVE:
                            leave_count += 1
                    else:
                        close()
                        block = [d.day_date]
                        leave_count = 1 if t == DayType.LEAVE else 0
            else:
                close()

        close()
        return periods

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
