# core/rh_rules/models/rest_period.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence


@dataclass(frozen=True)
class RestPeriod:
    """
    A consecutive block of REST days (DayType.REST).
    Minimal model for RH rules and analyzers.
    """
    days: Sequence[date]

    @property
    def start(self) -> date:
        return self.days[0]

    @property
    def end(self) -> date:
        return self.days[-1]

    @property
    def nb_jours(self) -> int:
        return len(self.days)

    def is_simple(self) -> bool:
        return self.nb_jours == 1

    def is_double(self) -> bool:
        return self.nb_jours == 2

    def is_triple(self) -> bool:
        return self.nb_jours == 3

    def is_4plus(self) -> bool:
        return self.nb_jours >= 4

    def is_rpsd(self) -> bool:
        """Saturday->Sunday inside the same rest period."""
        s = set(self.days)
        for d in self.days:
            if d.weekday() == 5 and date.fromordinal(d.toordinal() + 1) in s:
                return True
        return False

    def is_werp(self) -> bool:
        """Sat->Sun OR Sun->Mon inside the same rest period."""
        s = set(self.days)
        for d in self.days:
            if d.weekday() == 5 and date.fromordinal(d.toordinal() + 1) in s:
                return True
            if d.weekday() == 6 and date.fromordinal(d.toordinal() + 1) in s:
                return True
        return False
