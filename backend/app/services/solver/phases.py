from __future__ import annotations

from typing import Any

from ortools.sat.python import cp_model


class TraceCallback(cp_model.CpSolverSolutionCallback):
    """Collect first-feasible and best-objective trace points.

    Mutates only internal trace fields (``first_feasible_time``/``points``).
    """

    def __init__(self, understaff_var: cp_model.IntVar, stop_no_improve_after_seconds: float | None = None):
        super().__init__()
        self.understaff_var = understaff_var
        self.first_feasible_time = None
        self.points: list[tuple[float, float, int]] = []
        self.stop_no_improve_after_seconds = stop_no_improve_after_seconds
        self.last_improve_time = 0.0
        self.best_obj = None

    def on_solution_callback(self):
        t = float(self.WallTime())
        if self.first_feasible_time is None:
            self.first_feasible_time = t
            self.last_improve_time = t
        obj = float(self.ObjectiveValue())
        us = int(self.Value(self.understaff_var))
        improved = self.best_obj is None or obj < self.best_obj
        if improved:
            self.best_obj = obj
            self.last_improve_time = t
        if len(self.points) < 200 and (not self.points or improved or us < self.points[-1][2]):
            self.points.append((t, obj, us))
        if self.stop_no_improve_after_seconds is not None and (t - self.last_improve_time) >= self.stop_no_improve_after_seconds:
            self.StopSearch()


def solve_with_trace(
    solver: cp_model.CpSolver,
    mdl: cp_model.CpModel,
    cb: TraceCallback | None = None,
) -> int:
    """Solve a model with optional trace callback.

    Keeps legacy fallback behavior when callback signature is unsupported.
    """
    if cb is None:
        return solver.Solve(mdl)
    try:
        return solver.Solve(mdl, cb)
    except TypeError:
        return solver.Solve(mdl)
