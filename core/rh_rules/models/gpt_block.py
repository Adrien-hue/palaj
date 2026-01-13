# core/rh_rules/models/gpt_block.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from core.domain.enums.day_type import DayType
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.utils.rh_night import rh_day_is_nocturne
from core.rh_rules.utils.time_calculations import worked_minutes


@dataclass(frozen=True)
class GptBlock:
    """
    RH-first GPT block: consecutive working days (WORKING/ZCOT).
    """
    days: Sequence[RhDay]
    is_left_truncated: bool = False
    is_right_truncated: bool = False

    @property
    def start(self) -> date:
        return self.days[0].day_date

    @property
    def end(self) -> date:
        return self.days[-1].day_date

    @property
    def nb_jours(self) -> int:
        return len(self.days)

    @property
    def total_minutes(self) -> int:
        return sum(worked_minutes(d) for d in self.days)

    @property
    def has_zcot(self) -> bool:
        return any(d.day_type == DayType.ZCOT for d in self.days)

    @property
    def has_working(self) -> bool:
        return any(d.day_type == DayType.WORKING for d in self.days)

    @property
    def has_nocturne(self) -> bool:
        return any(rh_day_is_nocturne(d) for d in self.days)

    @property
    def is_truncated(self) -> bool:
        return self.is_left_truncated or self.is_right_truncated

    @property
    def is_complete(self) -> bool:
        return not self.is_truncated
