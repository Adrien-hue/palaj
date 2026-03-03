from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from datetime import time
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
    qualification_date_by_agent_poste: dict[tuple[int, int], date | None]
    existing_day_type_by_agent_day: dict[tuple[int, date], str]
    poste_ids: list[int]
    tranches: list["TrancheInfo"]
    coverage_demands: list["CoverageDemand"]
    gpt_context_days: list[date] = field(default_factory=list)
    existing_day_type_by_agent_day_ctx: dict[tuple[int, date], str] = field(default_factory=dict)
    existing_work_minutes_by_agent_day_ctx: dict[tuple[int, date], int] = field(default_factory=dict)
    existing_shift_start_end_by_agent_day_ctx: dict[tuple[int, date], tuple[int, int] | None] = field(default_factory=dict)
    quality_profile: str = "balanced"
    v3_strategy: str = "two_phase_lns"
    phase1_fraction: float | None = None
    phase1_seconds: float | None = None
    lns_iter_seconds: float | None = None
    lns_min_remaining_seconds: float | None = None
    lns_strict_improve: bool = True
    lns_max_days_to_relax: int | None = None
    min_lns_seconds: float | None = None
    phase2_max_fraction_of_remaining: float | None = None
    phase2_no_improve_seconds: float | None = None
    enable_decision_strategy: bool | None = None
    enable_symmetry_breaking: bool | None = None


class SolverFailureError(Exception):
    def __init__(self, message: str, stats: dict[str, Any] | None = None):
        super().__init__(message)
        self.stats = stats or {}


class InfeasibleError(SolverFailureError):
    pass


class TimeoutError(SolverFailureError):
    pass


@dataclass(frozen=True)
class TrancheInfo:
    id: int
    poste_id: int
    heure_debut: time = time(0, 0)
    heure_fin: time = time(0, 0)


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
