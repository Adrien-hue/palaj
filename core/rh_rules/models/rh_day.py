# core/rh_rules/models/rh_day.py
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from core.rh_rules.models.rh_interval import RhInterval

@dataclass(frozen=True)
class RhDay:
    agent_id: int
    day_date: date
    intervals: List[RhInterval]
    day_type: Optional[str] = None
