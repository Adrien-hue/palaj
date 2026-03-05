from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ortools.sat.python import cp_model


@dataclass
class SolveContext:
    """Immutable solve-scoped inputs and derived indexing helpers."""

    ordered_agent_ids: list[int]
    dates: list[Any]
    date_to_index: dict[Any, int]
    context_days: list[Any]
    ctx_date_to_index: dict[Any, int]
    in_window_ctx_indices: set[int]
    apply_gpt_rules: bool
    time_limit_seconds: float
    profile: str


@dataclass
class ModelArtifacts:
    """Container for CP-SAT model objects and variable mappings."""

    model: cp_model.CpModel
    y: dict[tuple[int, int, int], cp_model.IntVar] = field(default_factory=dict)
    vars_by_agent_day: dict[tuple[int, int], list[cp_model.IntVar]] = field(default_factory=dict)
    vars_by_demand: dict[tuple[int, int], list[cp_model.IntVar]] = field(default_factory=dict)
    run_vars: dict[tuple[int, int, int], cp_model.IntVar] = field(default_factory=dict)
    y_proto_idx: dict[tuple[int, int, int], int] = field(default_factory=dict)


@dataclass
class PhaseResult:
    """Result payload for a CP-SAT phase solve."""

    status_raw: str | None
    status_normalized: str | None
    status_int: int | None
    wall_time_seconds: float
    time_limit_reached: bool
    objective_value: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class SolveTimings:
    """Wall-time split used for flat/grouped stats."""

    model_build_wall_time_seconds: float = 0.0
    phase1_wall_time_seconds: float = 0.0
    phase2_wall_time_seconds: float = 0.0
    lns_total_wall_time_seconds: float = 0.0
