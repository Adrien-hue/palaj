from __future__ import annotations

from datetime import datetime, time, timedelta
from core.rh_rules.models.rh_day import RhDay

NIGHT_START = time(21, 30)
NIGHT_END = time(6, 30)


def is_night_interval(start: datetime, end: datetime) -> bool:
    """
    Returns True if [start, end] intersects the night window.
    Night window is 21:30 -> 06:30 (spans midnight).
    """
    if end <= start:
        return False

    # Build two night windows to cover crossing midnight.
    day = start.date()
    w1_start = datetime.combine(day, NIGHT_START)
    w1_end = datetime.combine(day + timedelta(days=1), NIGHT_END)

    day2 = (start + timedelta(days=1)).date()
    w2_start = datetime.combine(day2, NIGHT_START)
    w2_end = datetime.combine(day2 + timedelta(days=1), NIGHT_END)

    # Intersect check
    def intersects(a_start, a_end, b_start, b_end) -> bool:
        return max(a_start, b_start) < min(a_end, b_end)

    return intersects(start, end, w1_start, w1_end) or intersects(start, end, w2_start, w2_end)


def rh_day_is_nocturne(day: RhDay) -> bool:
    return any(is_night_interval(i.start, i.end) for i in day.intervals)
