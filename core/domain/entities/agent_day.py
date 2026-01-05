# core/domain/entities/agent_day.py
from __future__ import annotations
from datetime import date
from typing import List, Optional

from core.domain.enums.day_type import DayType

class AgentDay:
    def __init__(
        self,
        agent_id: int,
        day_date: date,
        day_type: DayType,
        description: Optional[str] = None,
        is_off_shift: bool = False,
    ):
        self.agent_id = agent_id
        self.day_date = day_date
        self.day_type = day_type
        self.description = description
        self.is_off_shift = is_off_shift

        self._tranche_ids: List[int] | None = None

    @property
    def tranche_ids(self) -> List[int]:
        return self._tranche_ids or []

    def set_tranche_ids(self, tranche_ids: List[int]) -> None:
        self._tranche_ids = tranche_ids
