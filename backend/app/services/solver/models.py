from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Optional


@dataclass(frozen=True)
class SolverInput:
    team_id: int
    start_date: date
    end_date: date
    seed: Optional[int]
    time_limit_seconds: int
    agent_ids: list[int]


@dataclass(frozen=True)
class SolverAgentDay:
    agent_id: int
    day_date: date
    day_type: str
    description: Optional[str] = None
    is_off_shift: bool = False


@dataclass(frozen=True)
class SolverAssignment:
    agent_id: int
    day_date: date
    tranche_id: int


@dataclass(frozen=True)
class SolverOutput:
    agent_days: list[SolverAgentDay]
    assignments: list[SolverAssignment]
    stats: dict[str, Any]
