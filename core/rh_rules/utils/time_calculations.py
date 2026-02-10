from __future__ import annotations

from datetime import datetime
from core.rh_rules.models.rh_day import RhDay


def amplitude_minutes(day: RhDay) -> int:
    if not day.intervals:
        return 0
    start: datetime = min(i.start for i in day.intervals)
    end: datetime = max(i.end for i in day.intervals)
    return int((end - start).total_seconds() / 60)

def worked_minutes(day: RhDay) -> int:
    if not day.is_working():
        return 0

    if day.forfait_minutes is not None:
        return int(day.forfait_minutes)

    if not day.intervals:
        return 0
    
    return sum(int((i.end - i.start).total_seconds() / 60) for i in day.intervals)