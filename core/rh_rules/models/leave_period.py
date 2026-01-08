# core/rh_rules/models/leave_period.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence


@dataclass(frozen=True)
class LeavePeriod:
    """
    RH leave period:
    - consecutive calendar days
    - allowed types: LEAVE and REST
    - must contain at least one LEAVE day
    """
    days: Sequence[date]
    leave_days: int  # number of LEAVE days within the period

    @property
    def start(self) -> date:
        return self.days[0]

    @property
    def end(self) -> date:
        return self.days[-1]

    @property
    def nb_jours(self) -> int:
        return len(self.days)
