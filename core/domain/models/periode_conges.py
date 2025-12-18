from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List

from core.domain.models.work_day import WorkDay
from core.domain.entities import TypeJour


@dataclass
class PeriodeConges:
    """
    Période de congés au sens RH SNCF :

    - regroupe des WorkDay **consécutifs** sur le calendrier
    - chaque jour est soit CONGE soit REPOS
    - la période doit contenir **au moins un jour CONGE**
    - les jours de REPOS ne cassent pas la période, ils en font partie

    Exemple :
        C C R C R  →  une seule PeriodeConges
        (C = congé, R = repos)
    """

    workdays: List[WorkDay]

    # -------------------------
    # Propriétés de base
    # -------------------------
    @property
    def jours(self) -> List[date]:
        return [wd.jour for wd in self.workdays]

    @property
    def start(self) -> date:
        return min(wd.jour for wd in self.workdays)

    @property
    def end(self) -> date:
        return max(wd.jour for wd in self.workdays)

    @property
    def nb_jours(self) -> int:
        """Nombre total de jours dans la période (congés + repos)."""
        # On suppose les jours distincts et consécutifs
        return len(self.workdays)

    @property
    def nb_conges(self) -> int:
        """Nombre de jours réellement en CONGE dans la période."""
        return sum(1 for wd in self.workdays if wd.type() == TypeJour.CONGE)

    # -------------------------
    # Qualification / affichage
    # -------------------------
    def label(self) -> str:
        return f"Période de congés {self.nb_jours}j ({self.nb_conges}j de congés)"

    def __str__(self) -> str:
        return f"{self.label()} du {self.start} au {self.end}"

    # -------------------------
    # Fabrique
    # -------------------------
    @classmethod
    def from_workdays(cls, workdays: List[WorkDay]) -> "PeriodeConges":
        """
        Construit une PeriodeConges à partir d'une liste de WorkDay.

        Vérifie :
        - liste non vide
        - jours triés et consécutifs (écart = 1 jour)
        - uniquement des jours CONGE ou REPOS
        - au moins un jour CONGE
        """
        if not workdays:
            raise ValueError("PeriodeConges.from_workdays() nécessite au moins un WorkDay.")

        # tri par date
        sorted_days = sorted(workdays, key=lambda wd: wd.jour)

        # vérification consécutive
        for prev, curr in zip(sorted_days, sorted_days[1:]):
            if (curr.jour - prev.jour).days != 1:
                raise ValueError(
                    f"WorkDays non consécutifs dans PeriodeConges : {prev.jour} → {curr.jour}"
                )

        # vérification des types
        for wd in sorted_days:
            t = wd.type()
            if t not in (TypeJour.CONGE, TypeJour.REPOS):
                raise ValueError(
                    f"PeriodeConges ne peut contenir que CONGE/REPOS (trouvé {t} le {wd.jour})"
                )

        # au moins un congé réel
        nb_conges = sum(1 for wd in sorted_days if wd.type() == TypeJour.CONGE)
        if nb_conges == 0:
            raise ValueError("PeriodeConges doit contenir au moins un jour CONGE.")

        return cls(workdays=sorted_days)
