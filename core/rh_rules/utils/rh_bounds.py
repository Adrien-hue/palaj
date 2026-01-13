from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple
from core.rh_rules.models.rh_day import RhDay

def work_bounds(day: RhDay) -> Optional[Tuple[datetime, datetime]]:
    if not day.intervals:
        return None
    start = min(i.start for i in day.intervals)
    end = max(i.end for i in day.intervals)
    return start, end
