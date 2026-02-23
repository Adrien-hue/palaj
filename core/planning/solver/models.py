from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, Set, Tuple, List


class PlanningMode(str, Enum):
    PLAN = "PLAN"
    REPAIR = "REPAIR"


@dataclass(frozen=True, slots=True)
class Need:
    """Besoin canonique (par date) consumé par le solveur (lot 2)."""
    poste_id: int
    date: date
    tranche_id: int
    required_count: int

    @property
    def key(self) -> Tuple[int, date, int]:
        return (self.poste_id, self.date, self.tranche_id)


@dataclass(frozen=True, slots=True)
class SolverAgent:
    id: int
    qualifications: Set[int]
    unavailable_dates: Set[date]


@dataclass(frozen=True, slots=True)
class SolverSlot:
    id: int
    poste_id: int
    date: date
    tranche_id: int

    @property
    def key(self) -> Tuple[int, date, int]:
        return (self.poste_id, self.date, self.tranche_id)


@dataclass(frozen=True, slots=True)
class BaselineGroup:
    poste_id: int
    date: date
    tranche_id: int
    agents: Set[int]

    @property
    def key(self) -> Tuple[int, date, int]:
        return (self.poste_id, self.date, self.tranche_id)


class LockType(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    NONE = "NONE"


@dataclass(frozen=True, slots=True)
class SlotLock:
    slot_id: int
    lock_type: LockType
    agent_id: Optional[int] = None


@dataclass(frozen=True, slots=True)
class PlanningInstance:
    agents: List[SolverAgent]
    slots: List[SolverSlot]
    baseline_groups: List[BaselineGroup]
    locks: List[SlotLock]
    mode: PlanningMode
