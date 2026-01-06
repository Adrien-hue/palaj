# core/rh_rules/models/rh_interval.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class RhInterval:
    start: datetime
    end: datetime
    tranche_id: Optional[int] = None
    poste_id: Optional[int] = None