# core/domain/entities/agent_day.py
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional

from core.domain.entities import Agent, Tranche

class DayType(str, Enum):
    ABSENT = "absent"
    LEAVE = "leave"
    OFF_SHIFT = "off_shift"
    REST = "rest"
    UNKNOWN = "unknown"
    WORKING = "working"
    ZCOT = "zcot"
    
@dataclass(frozen=True)
class AgentDay:
    agent: Agent
    date: date

    day_type: DayType
    description: Optional[str] = None

    # Regular work
    shifts: List[Tranche] = field(default_factory=list)

    # Off-shift work (ex: ZCOT)
    is_off_shift: bool = False
