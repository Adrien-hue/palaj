# core/domain/ennums/day_type.py
from enum import Enum

class DayType(str, Enum):
    ABSENT = "absent"
    WORKING = "working"
    REST = "rest"
    LEAVE = "leave"
    OFF_SHIFT = "off_shift"
    ZCOT = "zcot"
    UNKNOWN = "unknown"