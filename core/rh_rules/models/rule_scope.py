from __future__ import annotations
from enum import Enum

class RuleScope(str, Enum):
    DAY = "day"
    PERIOD = "period"
