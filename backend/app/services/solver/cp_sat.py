from __future__ import annotations

from typing import Any

from ortools.sat.python import cp_model


def normalize_status(raw_status: int, wall_time: float, budget_seconds: float) -> tuple[str, str, bool]:
    """Map raw CP-SAT status to the solver timeout convention.

    Pure helper: does not mutate solver stats.
    """
    if raw_status == cp_model.OPTIMAL:
        raw = "OPTIMAL"
    elif raw_status == cp_model.FEASIBLE:
        raw = "FEASIBLE"
    elif raw_status == cp_model.INFEASIBLE:
        raw = "INFEASIBLE"
    elif raw_status == cp_model.MODEL_INVALID:
        raw = "MODEL_INVALID"
    elif raw_status == cp_model.UNKNOWN:
        raw = "UNKNOWN"
    else:
        raw = "INFEASIBLE"
    time_limit_reached = False
    if budget_seconds > 0:
        if raw_status == cp_model.OPTIMAL:
            time_limit_reached = False
        else:
            time_limit_reached = (raw_status == cp_model.FEASIBLE) or (wall_time >= budget_seconds * 0.95)
    normalized = "TIMEOUT" if time_limit_reached else raw
    return raw, normalized, bool(time_limit_reached)


def configure_solver(*, budget_seconds: float, time_limit_seconds: float, seed: int) -> cp_model.CpSolver:
    """Build a configured single-thread deterministic CP-SAT solver.

    CP-SAT config only; this helper does not write result stats.
    """
    solver = cp_model.CpSolver()
    if budget_seconds > 0:
        solver.parameters.max_time_in_seconds = budget_seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = int(seed or 0)
    return solver


def effective_cp_sat_params(
    *,
    solver: cp_model.CpSolver,
    budget_seconds: float,
    profile: str,
    seed: int,
    time_limit_seconds: float,
) -> dict[str, Any]:
    """Return effective CP-SAT parameter snapshot for stats.

    Snapshot-only helper; caller owns any stats mutation.
    """
    del profile, seed, time_limit_seconds
    params: dict[str, Any] = {
        "max_time_in_seconds": float(getattr(solver.parameters, "max_time_in_seconds", 0.0) or 0.0),
        "num_search_workers": int(getattr(solver.parameters, "num_search_workers", 0) or 0),
        "random_seed": int(getattr(solver.parameters, "random_seed", 0) or 0),
    }
    optional_numeric = {
        "max_number_of_conflicts": int(getattr(solver.parameters, "max_number_of_conflicts", 0) or 0),
        "cp_model_probing_level": int(getattr(solver.parameters, "cp_model_probing_level", 0) or 0),
        "symmetry_level": int(getattr(solver.parameters, "symmetry_level", 0) or 0),
        "linearization_level": int(getattr(solver.parameters, "linearization_level", 0) or 0),
    }
    for key, value in optional_numeric.items():
        if value != 0:
            params[key] = value
    if bool(getattr(solver.parameters, "log_search_progress", False)):
        params["log_search_progress"] = True
    if bool(getattr(solver.parameters, "cp_model_presolve", True)) is False:
        params["cp_model_presolve"] = False
    params["budget_seconds_requested"] = float(budget_seconds)
    return params
