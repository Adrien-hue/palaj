from __future__ import annotations

from datetime import datetime
from core.rh_rules.models.rh_day import RhDay


def amplitude_minutes(day: RhDay) -> int:
    if not day.intervals:
        return 0
    start: datetime = min(i.start for i in day.intervals)
    end: datetime = max(i.end for i in day.intervals)
    return int((end - start).total_seconds() / 60)
