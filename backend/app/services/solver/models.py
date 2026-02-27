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
    absences: set[tuple[int, date]]
    qualified_postes_by_agent: dict[int, tuple[int, ...]]
    poste_ids: list[int]
    tranches: list["TrancheInfo"]
    coverage_demands: list["CoverageDemand"]


@dataclass(frozen=True)
class TrancheInfo:
    id: int
    poste_id: int


@dataclass(frozen=True)
class CoverageDemand:
    day_date: date
    tranche_id: int
    required_count: int
    poste_id: Optional[int] = None


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
