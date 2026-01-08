from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import List

from core.domain.enums.day_type import DayType
from core.rh_rules.models.rh_day import RhDay
from core.domain.models.work_day import WorkDay
from core.rh_rules.adapters.workday_adapter import rh_day_from_workday


@dataclass
class PeriodeConges:
    """
    Période de congés au sens RH SNCF :

    - jours consécutifs sur le calendrier
    - chaque jour est soit LEAVE soit REST
    - contient au moins un jour LEAVE
    """

    days: List[RhDay]

    @property
    def jours(self) -> List[date]:
        return [d.day_date for d in self.days]

    @property
    def start(self) -> date:
        return min(d.day_date for d in self.days)

    @property
    def end(self) -> date:
        return max(d.day_date for d in self.days)

    @property
    def nb_jours(self) -> int:
        return len(self.days)

    @property
    def nb_conges(self) -> int:
        return sum(1 for d in self.days if d.day_type == DayType.LEAVE)

    def label(self) -> str:
        return f"Période de congés {self.nb_jours}j ({self.nb_conges}j de congés)"

    def __str__(self) -> str:
        return f"{self.label()} du {self.start} au {self.end}"

    @classmethod
    def from_rh_days(cls, days: List[RhDay]) -> "PeriodeConges":
        if not days:
            raise ValueError("PeriodeConges.from_rh_days() nécessite au moins un RhDay.")

        sorted_days = sorted(days, key=lambda d: d.day_date)

        for prev, curr in zip(sorted_days, sorted_days[1:]):
            if (curr.day_date - prev.day_date).days != 1:
                raise ValueError(
                    f"Jours non consécutifs dans PeriodeConges : {prev.day_date} → {curr.day_date}"
                )

        for d in sorted_days:
            if d.day_type not in (DayType.LEAVE, DayType.REST):
                raise ValueError(
                    f"PeriodeConges ne peut contenir que LEAVE/REST (trouvé {d.day_type} le {d.day_date})"
                )

        if sum(1 for d in sorted_days if d.day_type == DayType.LEAVE) == 0:
            raise ValueError("PeriodeConges doit contenir au moins un jour LEAVE.")

        return cls(days=sorted_days)

    @classmethod
    def from_workdays(cls, workdays: List[WorkDay]) -> "PeriodeConges":
        """
        Compat legacy : convertit WorkDay -> RhDay puis délègue.
        """
        if not workdays:
            raise ValueError("PeriodeConges.from_workdays() nécessite au moins un WorkDay.")

        rh_days = [rh_day_from_workday(agent_id=0, wd=wd) for wd in workdays]
        return cls.from_rh_days(rh_days)
