from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time
from typing import Any, Callable

from ortools.sat.python import cp_model

from backend.app.services.solver.constants import LNS_RECENT_STATUS_WINDOW
from backend.app.services.solver.models import SolverInput


@dataclass
class LnsRunResult:
    best_solution: dict[str, Any] | None
    lns_iterations: int
    lns_accept_count: int
    lns_best_improvement_understaff: int
    lns_best_improvement_objective: int
    lns_neighborhoods_tried: dict[str, int]


class LnsRunner:
    def __init__(self, *, max_lns_history_items: int) -> None:
        self.max_lns_history_items = int(max_lns_history_items)

    def run(
        self,
        *,
        best_solution: dict[str, Any] | None,
        stats: dict[str, Any],
        solver_input: SolverInput,
        demand_records: list[dict[str, Any]],
        dates: list[Any],
        started_at: float,
        time_limit_seconds: float,
        lns_enabled: bool,
        lns_min_remaining_seconds: float,
        lns_iter_seconds: float,
        lns_strict_improve: bool,
        lns_max_days_to_relax: int,
        lns_neighborhood_mode: str,
        min_remaining_seconds_to_run_iter: float,
        lns_iter_overhead_seconds: float,
        min_lns_cp_sat_time_limit_seconds: float,
        model: cp_model.CpModel,
        y_keys: list[tuple[int, int, int]],
        combo_by_id: dict[int, Any],
        y_proto_idx: dict[tuple[int, int, int], int],
        run_vars: dict[tuple[int, int, int], cp_model.IntVar],
        _new_solver: Callable[[float], cp_model.CpSolver],
        _effective_cp_sat_params: Callable[[cp_model.CpSolver, float], dict[str, Any]],
        _normalize_status: Callable[[Any, float, float], tuple[str, str, bool]],
        _extract_solution: Callable[[cp_model.CpSolver], dict[str, Any]],
    ) -> LnsRunResult:
        """Execute the deterministic LNS phase for an existing incumbent solution.

        Args:
            best_solution: Current incumbent solution dict, or ``None`` when no feasible
                incumbent exists yet.
            stats: Mutable flat result stats dict from ``OrtoolsSolver``. This method
                updates only LNS-related flat keys (``lns_*``) and
                ``cp_sat_params_effective["lns"]`` when an LNS CP-SAT solve is launched.
            solver_input/demand_records/dates: Input data required for neighborhood
                selection and deterministic poste/day ordering.
            started_at/time_limit_seconds: Global solve clock context shared with
                ``OrtoolsSolver`` for budget guards and timings.
            lns_* parameters: LNS tuning and guardrail values already parsed by
                ``OrtoolsSolver``.
            model/y_keys/combo_by_id/y_proto_idx/run_vars: Solver model and variable
                mappings needed to rebuild per-iteration relaxed models.
            _new_solver/_effective_cp_sat_params/_normalize_status/_extract_solution:
                Existing solver helpers injected by ``OrtoolsSolver`` to preserve behavior.

        Returns:
            ``LnsRunResult`` containing the possibly updated best solution and aggregate
            counters consumed by ``OrtoolsSolver`` (iterations, accept count,
            improvements, neighborhoods tried).

        Side effects and invariants:
            - Writes/refreshes only the flat ``lns_*`` stats contract (including
              ``lns_iteration_history`` as a list) plus
              ``cp_sat_params_effective["lns"]`` when an LNS solve is launched.
            - Does not modify non-LNS families (coverage/model/objective/
              solution_quality), which remain owned by ``OrtoolsSolver`` and
              ``StatsCollector``.
            - Resets ``lns_iter_time_limit_seconds_effective_last`` to ``None`` at the
              beginning of every LNS attempt.
            - Leaves ``lns_iter_time_limit_seconds_effective_last`` as ``None`` when
              an early-stop happens before launching the iteration CP-SAT solve.
        """
        lns_iterations = 0
        lns_accept_count = 0
        lns_best_improvement_understaff = 0
        lns_best_improvement_objective = 0
        lns_neighborhoods_tried = {str(pid): 0 for pid in sorted(set(solver_input.poste_ids))}
        lns_iteration_history: list[dict[str, object]] = []
        lns_model_rebuild_total = 0.0
        lns_solve_total = 0.0
        lns_iter_solve_walls: list[float] = []
        lns_mode_used_counts = {"poste_only": 0, "poste_plus_one": 0, "top_days_global": 0, "poste_plus_one_top_days": 0, "mixed": 0}
        lns_selected_postes_last: list[int] = []
        lns_relaxed_days_count_last = 0
        lns_fixed_days_count_last = 0
        lns_fixed_y_count_last = 0
        lns_relaxed_y_count_last = 0
        lns_fixed_runs_count_last = 0
        lns_relaxed_runs_count_last = 0
        lns_fixed_vars_count_last = 0
        lns_relaxed_vars_count_last = 0
        lns_solver_time_limit_seconds_applied = 0.0
        lns_unknown_count_total = 0
        lns_no_solution_count_total = 0
        lns_fallback_triggered = False
        lns_fallback_reason = None
        lns_effective_mode_last = lns_neighborhood_mode
        lns_poste_plus_one_top_days_selected_sample: list[str] = []
        lns_poste_plus_one_top_days_k = 0
        lns_recent_statuses: deque[bool] = deque(maxlen=LNS_RECENT_STATUS_WINDOW)
        lns_recent_accepts: deque[bool] = deque(maxlen=LNS_RECENT_STATUS_WINDOW)
        lns_fallback_after_iterations: int | None = None
        lns_fallback_iteration_index: int | None = None
        lns_accept_count_at_fallback = 0
        lns_last_accept_iteration_index: int | None = None
        lns_last_accept_t: float | None = None
        lns_early_stop_triggered = False
        lns_early_stop_reason = None
        lns_remaining_budget_seconds_at_stop: float | None = None
        lns_required_budget_seconds_to_start_iter: float | None = None
        lns_intended_iter_time_limit_seconds_last: float | None = None
        lns_iter_time_limit_seconds_effective_last: float | None = None
        lns_history_max_items = self.max_lns_history_items
        lns_history_truncated = False

        def _append_lns_history(entry: dict[str, object]) -> None:
            # No trimming here; payload caps are handled in StatsCollector.
            lns_iteration_history.append(entry)

        lns_start_remaining = max(0.0, (time_limit_seconds - (time.monotonic() - started_at))) if lns_enabled and time_limit_seconds > 0 else 0.0
        if lns_enabled and best_solution is not None:
            poste_ids_sorted = sorted(set(solver_input.poste_ids))
            demanded_poste_ids = sorted({int(rec["poste_id"]) for rec in demand_records})
            mixed_cycle = ["poste_only", "poste_plus_one", "top_days_global"]

            def _poste_priority_order() -> list[int]:
                ordered = sorted(
                    poste_ids_sorted,
                    key=lambda pid: (
                        -int(best_solution.get("understaff_by_poste_unweighted", {}).get(pid, 0)),
                        -int(best_solution.get("understaff_by_poste_weighted", {}).get(pid, 0)),
                        pid,
                    ),
                )
                if all(int(best_solution.get("understaff_by_poste_unweighted", {}).get(pid, 0)) == 0 for pid in ordered):
                    ordered = poste_ids_sorted
                return [pid for pid in ordered if pid in demanded_poste_ids]

            def _select_days_for_postes(selected_postes: list[int]) -> set[int]:
                scored: list[tuple[int, int, int]] = []
                for (pid, di), us in best_solution.get("understaff_by_poste_day", {}).items():
                    if pid in selected_postes and us > 0:
                        weighted = us * max(1, int(best_solution.get("understaff_by_poste_weighted", {}).get(pid, us)) // max(1, int(best_solution.get("understaff_by_poste_unweighted", {}).get(pid, us))))
                        scored.append((int(us), int(weighted), int(di)))
                scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
                base_days = [di for (_us, _w, di) in scored[:lns_max_days_to_relax]]
                if not base_days:
                    base_days = list(range(min(len(dates), lns_max_days_to_relax)))
                selected_days: set[int] = set()
                for di in base_days:
                    for dd in range(max(0, di - 2), min(len(dates), di + 3)):
                        selected_days.add(dd)
                if len(selected_days) > lns_max_days_to_relax:
                    selected_days = set(sorted(selected_days)[:lns_max_days_to_relax])
                return selected_days

            def _select_days_global() -> set[int]:
                day_scored = [
                    (int(best_solution.get("understaff_by_day_unweighted", {}).get(di, 0)), int(best_solution.get("understaff_by_day_weighted", {}).get(di, 0)), di)
                    for di in range(len(dates))
                ]
                day_scored.sort(key=lambda item: (-item[0], -item[1], item[2]))
                base_days = [di for (u, _w, di) in day_scored if u > 0][:lns_max_days_to_relax]
                if not base_days:
                    base_days = list(range(min(len(dates), lns_max_days_to_relax)))
                return set(base_days)

            def _select_top_days_weighted(k: int) -> set[int]:
                k = max(1, min(len(dates), int(k)))
                day_scored = [
                    (int(best_solution.get("understaff_by_day_weighted", {}).get(di, 0)), dates[di], di)
                    for di in range(len(dates))
                ]
                day_scored.sort(key=lambda item: (-item[0], item[1]))
                selected = [di for (_w, _date, di) in day_scored[:k]]
                if not selected:
                    selected = list(range(k))
                return set(selected)

            while True:
                elapsed = time.monotonic() - started_at
                remaining = (time_limit_seconds - elapsed) if time_limit_seconds > 0 else 0.0
                if remaining <= max(lns_min_remaining_seconds, 0.0):
                    break

                lns_iter_time_limit_seconds_effective_last = None

                intended_iter_time_limit_seconds = min(lns_iter_seconds, remaining)
                lns_intended_iter_time_limit_seconds_last = float(intended_iter_time_limit_seconds)
                required_budget_to_start_iter = max(
                    min_remaining_seconds_to_run_iter,
                    intended_iter_time_limit_seconds + lns_iter_overhead_seconds,
                )
                lns_required_budget_seconds_to_start_iter = float(required_budget_to_start_iter)

                if remaining < required_budget_to_start_iter:
                    lns_early_stop_triggered = True
                    lns_early_stop_reason = "remaining_budget_too_small_for_iter"
                    lns_remaining_budget_seconds_at_stop = float(remaining)
                    break

                budget = min(
                    intended_iter_time_limit_seconds,
                    max(0.0, remaining - lns_iter_overhead_seconds),
                )
                if budget < min_lns_cp_sat_time_limit_seconds:
                    lns_early_stop_triggered = True
                    lns_early_stop_reason = "remaining_budget_too_small_for_iter"
                    lns_remaining_budget_seconds_at_stop = float(remaining)
                    break
                if budget <= 0:
                    break

                requested_mode = lns_neighborhood_mode
                effective_mode = requested_mode
                if requested_mode == "mixed":
                    effective_mode = mixed_cycle[lns_iterations % len(mixed_cycle)]

                if len(lns_recent_statuses) == lns_recent_statuses.maxlen:
                    unknown_ratio = sum(1 for has_solution in lns_recent_statuses if not has_solution) / len(lns_recent_statuses)
                    if unknown_ratio > 0.8 and requested_mode != "poste_plus_one":
                        effective_mode = "poste_plus_one"
                        lns_fallback_triggered = True
                        lns_fallback_reason = "too_many_unknown"
                        if lns_fallback_after_iterations is None:
                            lns_fallback_after_iterations = int(lns_iterations)
                        if lns_fallback_iteration_index is None:
                            lns_fallback_iteration_index = int(lns_iterations)
                            lns_accept_count_at_fallback = int(lns_accept_count)
                    elif sum(1 for accepted in lns_recent_accepts if accepted) == 0 and requested_mode in {"top_days_global", "poste_plus_one_top_days"}:
                        effective_mode = "poste_plus_one"
                        lns_fallback_triggered = True
                        lns_fallback_reason = "no_acceptance_in_requested_mode"
                        if lns_fallback_after_iterations is None:
                            lns_fallback_after_iterations = int(lns_iterations)
                        if lns_fallback_iteration_index is None:
                            lns_fallback_iteration_index = int(lns_iterations)
                            lns_accept_count_at_fallback = int(lns_accept_count)

                lns_effective_mode_last = effective_mode
                lns_mode_used_counts[effective_mode] = lns_mode_used_counts.get(effective_mode, 0) + 1

                poste_priority = _poste_priority_order()
                if not poste_priority:
                    break

                selected_postes: list[int]
                if effective_mode in {"poste_plus_one", "poste_plus_one_top_days"}:
                    selected_postes = poste_priority[:2]
                elif effective_mode == "top_days_global":
                    selected_postes = poste_ids_sorted
                else:
                    selected_postes = poste_priority[:1]

                poste_id = selected_postes[0]
                stats["lns_last_selected_poste_id"] = poste_id
                lns_selected_postes_last = [int(pid) for pid in selected_postes]
                for pid in selected_postes:
                    lns_neighborhoods_tried[str(pid)] = lns_neighborhoods_tried.get(str(pid), 0) + 1

                if effective_mode == "top_days_global":
                    selected_days = _select_days_global()
                elif effective_mode == "poste_plus_one_top_days":
                    selected_days = _select_top_days_weighted(lns_max_days_to_relax)
                    lns_poste_plus_one_top_days_k = len(selected_days)
                    lns_poste_plus_one_top_days_selected_sample = [dates[di].isoformat() for di in sorted(selected_days)[:10]]
                else:
                    selected_days = _select_days_for_postes(selected_postes)
                lns_relaxed_days_count_last = len(selected_days)
                lns_fixed_days_count_last = max(0, len(dates) - lns_relaxed_days_count_last)

                relaxed = set()
                for (aid, di, cid) in y_keys:
                    combo = combo_by_id[cid]
                    if di not in selected_days:
                        continue
                    if effective_mode == "top_days_global" or combo.poste_id in selected_postes:
                        relaxed.add((aid, di, cid))
                lns_relaxed_y_count_last = len(relaxed)
                lns_fixed_y_count_last = len(y_keys) - lns_relaxed_y_count_last

                relaxed_runs = set()
                if run_vars:
                    for (aid, si, ei) in run_vars.keys():
                        if any(di in selected_days for di in range(si, ei + 1)):
                            relaxed_runs.add((aid, si, ei))
                lns_relaxed_runs_count_last = len(relaxed_runs)
                lns_fixed_runs_count_last = len(run_vars) - lns_relaxed_runs_count_last
                lns_relaxed_vars_count_last = int(lns_relaxed_y_count_last + lns_relaxed_runs_count_last)
                lns_fixed_vars_count_last = int(lns_fixed_y_count_last + lns_fixed_runs_count_last)

                rebuild_started = time.monotonic()
                lns_model = model.Clone()
                lns_y = {key: lns_model.GetBoolVarFromProtoIndex(y_proto_idx[key]) for key in y_keys}
                for key in y_keys:
                    if key in relaxed:
                        continue
                    lns_model.Add(lns_y[key] == int(best_solution["assignment_map"][key]))
                if run_vars:
                    lns_run = {(aid, si, ei): lns_model.GetBoolVarFromProtoIndex(run_vars[(aid, si, ei)].Index()) for (aid, si, ei) in run_vars}
                    for key in sorted(run_vars.keys()):
                        if key in relaxed_runs:
                            continue
                        lns_model.Add(lns_run[key] == int(best_solution.get("run_assignment_map", {}).get(key, 0)))
                lns_model.ClearHints()
                for key in y_keys:
                    lns_model.AddHint(lns_y[key], int(best_solution["assignment_map"][key]))
                if run_vars:
                    for key in sorted(run_vars.keys()):
                        lns_model.AddHint(lns_run[key], int(best_solution.get("run_assignment_map", {}).get(key, 0)))
                lns_model_rebuild_total += (time.monotonic() - rebuild_started)

                validate_message = lns_model.Validate()
                validate_message_present = bool(validate_message)
                if validate_message_present:
                    msg = str(validate_message)
                    stats["lns_model_invalid"] = True
                    lns_no_solution_count_total += 1
                    stats["lns_iter_has_solution"] = False
                    stats["lns_iter_status_raw"] = "MODEL_INVALID"
                    stats["lns_iter_status_int"] = int(cp_model.MODEL_INVALID)
                    stats["lns_iter_objective_value"] = None
                    stats["lns_iter_understaff_total_unweighted"] = None
                    stats["lns_iter_validate_message_present"] = True
                    stats["lns_model_invalid_message"] = msg[:1000]
                    stats["lns_model_invalid_iteration_index"] = lns_iterations
                    _append_lns_history(
                        {
                            "t": round(float(time.monotonic() - started_at), 3),
                            "poste_id": poste_id,
                            "selected_postes": [int(pid) for pid in selected_postes],
                            "relaxed_days_count": len(selected_days),
                            "status_raw": "MODEL_INVALID",
                            "status_int": int(cp_model.MODEL_INVALID),
                            "has_solution": False,
                            "lns_iter_has_solution": False,
                            "neighborhood_mode_effective": effective_mode,
                            "lns_iter_status_raw": "MODEL_INVALID",
                            "lns_iter_status_int": int(cp_model.MODEL_INVALID),
                            "validate_message_present": True,
                            "lns_iter_validate_message_present": True,
                            "solve_wall_time_seconds_iter": 0.0,
                            "accepted": False,
                            "fixed_y_count": int(lns_fixed_y_count_last),
                            "relaxed_y_count": int(lns_relaxed_y_count_last),
                            "fixed_runs_count": int(lns_fixed_runs_count_last),
                            "relaxed_runs_count": int(lns_relaxed_runs_count_last),
                            "understaff_total_unweighted": None,
                            "objective_value": None,
                            "lns_iter_understaff_total_unweighted": None,
                            "lns_iter_objective_value": None,
                        }
                    )
                    break

                lns_iter_time_limit_seconds_effective_last = float(budget)
                lns_solver = _new_solver(budget)
                lns_solver_time_limit_seconds_applied = budget
                stats.setdefault("cp_sat_params_effective", {})["lns"] = _effective_cp_sat_params(lns_solver, budget)
                lns_solve_started = time.monotonic()
                status_lns = lns_solver.Solve(lns_model)
                iter_solve_wall = float(time.monotonic() - lns_solve_started)
                lns_solve_total += iter_solve_wall
                lns_iter_solve_walls.append(iter_solve_wall)
                lns_iterations += 1
                raw_lns, _normalized_lns, _timeout_lns = _normalize_status(status_lns, iter_solve_wall, budget)
                has_solution = status_lns in (cp_model.OPTIMAL, cp_model.FEASIBLE)
                if raw_lns == "UNKNOWN":
                    lns_unknown_count_total += 1
                stats["lns_iter_has_solution"] = bool(has_solution)
                stats["lns_iter_status_raw"] = raw_lns
                stats["lns_iter_status_int"] = int(status_lns)
                stats["lns_iter_validate_message_present"] = bool(validate_message_present)
                if raw_lns in {"UNKNOWN", "INFEASIBLE"}:
                    lns_no_solution_count_total += 1

                accepted = False
                cand_understaff = None
                cand_obj = None
                if has_solution:
                    cand = _extract_solution(lns_solver)
                    cand_understaff = cand["understaff_total_unweighted"]
                    cand_obj = cand["objective_value"]
                    cur_pair = (best_solution["understaff_total_unweighted"], best_solution["objective_value"])
                    cand_pair = (cand["understaff_total_unweighted"], cand["objective_value"])
                    improved = (cand_pair < cur_pair) if lns_strict_improve else (cand_pair <= cur_pair)
                    if improved:
                        prev_u = best_solution["understaff_total_unweighted"]
                        prev_o = best_solution["objective_value"]
                        best_solution = cand
                        accepted = True
                        lns_accept_count += 1
                        lns_last_accept_iteration_index = int(lns_iterations - 1)
                        lns_last_accept_t = float(time.monotonic() - started_at)
                        lns_best_improvement_understaff = max(lns_best_improvement_understaff, prev_u - cand["understaff_total_unweighted"])
                        lns_best_improvement_objective = max(lns_best_improvement_objective, prev_o - cand["objective_value"])

                stats["lns_iter_objective_value"] = int(cand_obj) if cand_obj is not None else None
                stats["lns_iter_understaff_total_unweighted"] = int(cand_understaff) if cand_understaff is not None else None
                lns_recent_statuses.append(has_solution)
                lns_recent_accepts.append(accepted)

                _append_lns_history(
                    {
                        "t": round(float(time.monotonic() - started_at), 3),
                        "poste_id": poste_id,
                        "selected_postes": [int(pid) for pid in selected_postes],
                        "relaxed_days_count": len(selected_days),
                        "status_raw": raw_lns,
                        "status_int": int(status_lns),
                        "lns_iter_status_raw": raw_lns,
                        "lns_iter_status_int": int(status_lns),
                        "has_solution": bool(has_solution),
                        "lns_iter_has_solution": bool(has_solution),
                        "neighborhood_mode_effective": effective_mode,
                        "validate_message_present": validate_message_present,
                        "lns_iter_validate_message_present": bool(validate_message_present),
                        "solve_wall_time_seconds_iter": round(iter_solve_wall, 6),
                        "accepted": accepted,
                        "fixed_y_count": int(lns_fixed_y_count_last),
                        "relaxed_y_count": int(lns_relaxed_y_count_last),
                        "fixed_runs_count": int(lns_fixed_runs_count_last),
                        "relaxed_runs_count": int(lns_relaxed_runs_count_last),
                        "understaff_total_unweighted": cand_understaff,
                        "objective_value": cand_obj,
                        "lns_iter_understaff_total_unweighted": cand_understaff,
                        "lns_iter_objective_value": cand_obj,
                    }
                )

        stats["lns_iteration_history"] = lns_iteration_history
        stats["lns_model_rebuild_wall_time_seconds_total"] = float(lns_model_rebuild_total)
        stats["lns_solve_wall_time_seconds_total"] = float(lns_solve_total)
        stats["lns_iterations_time_budget_max"] = int(lns_start_remaining // lns_iter_seconds) if lns_enabled and lns_iter_seconds > 0 else 0
        stats["lns_iterations_actual"] = int(lns_iterations)
        stats["lns_avg_solve_wall_time_seconds_iter"] = float((sum(lns_iter_solve_walls) / len(lns_iter_solve_walls)) if lns_iter_solve_walls else 0.0)
        stats["lns_min_solve_wall_time_seconds_iter"] = float(min(lns_iter_solve_walls)) if lns_iter_solve_walls else 0.0
        stats["lns_max_solve_wall_time_seconds_iter"] = float(max(lns_iter_solve_walls)) if lns_iter_solve_walls else 0.0
        stats["lns_solver_time_limit_seconds_applied"] = float(lns_solver_time_limit_seconds_applied)
        stats["lns_neighborhood_mode_used_counts"] = {k: int(v) for k, v in lns_mode_used_counts.items() if v > 0}
        stats["lns_selected_postes_last"] = lns_selected_postes_last
        stats["lns_relaxed_days_count_last"] = int(lns_relaxed_days_count_last)
        stats["lns_fixed_days_count_last"] = int(lns_fixed_days_count_last)
        stats["lns_fixed_y_count_last"] = int(lns_fixed_y_count_last)
        stats["lns_relaxed_y_count_last"] = int(lns_relaxed_y_count_last)
        stats["lns_fixed_vars_count_last"] = int(lns_fixed_vars_count_last)
        stats["lns_relaxed_vars_count_last"] = int(lns_relaxed_vars_count_last)
        stats["lns_fixed_runs_count_last"] = int(lns_fixed_runs_count_last)
        stats["lns_relaxed_runs_count_last"] = int(lns_relaxed_runs_count_last)
        stats["lns_unknown_count_total"] = int(lns_unknown_count_total)
        stats["lns_no_solution_count_total"] = int(lns_no_solution_count_total)
        stats["lns_fallback_triggered"] = bool(lns_fallback_triggered)
        stats["lns_fallback_reason"] = lns_fallback_reason
        stats["lns_fallback_after_iterations"] = lns_fallback_after_iterations
        stats["lns_fallback_iteration_index"] = lns_fallback_iteration_index
        stats["lns_accept_count_at_fallback"] = int(lns_accept_count_at_fallback if lns_fallback_iteration_index is not None else lns_accept_count)
        stats["lns_last_accept_iteration_index"] = int(lns_last_accept_iteration_index) if lns_last_accept_iteration_index is not None else None
        stats["lns_last_accept_t"] = float(lns_last_accept_t) if lns_last_accept_t is not None else None
        stats["lns_early_stop_triggered"] = bool(lns_early_stop_triggered)
        stats["lns_early_stop_reason"] = lns_early_stop_reason
        stats["lns_remaining_budget_seconds_at_stop"] = float(lns_remaining_budget_seconds_at_stop) if lns_remaining_budget_seconds_at_stop is not None else None
        stats["lns_min_remaining_seconds_to_run_iter"] = float(min_remaining_seconds_to_run_iter)
        stats["lns_iter_overhead_seconds"] = float(lns_iter_overhead_seconds)
        stats["lns_required_budget_seconds_to_start_iter"] = (
            float(lns_required_budget_seconds_to_start_iter)
            if lns_required_budget_seconds_to_start_iter is not None
            else None
        )
        stats["lns_intended_iter_time_limit_seconds_last"] = (
            float(lns_intended_iter_time_limit_seconds_last)
            if lns_intended_iter_time_limit_seconds_last is not None
            else None
        )
        stats["lns_iter_time_limit_seconds_effective_last"] = (
            float(lns_iter_time_limit_seconds_effective_last)
            if lns_iter_time_limit_seconds_effective_last is not None
            else None
        )
        stats["lns_iter_time_limit_seconds_min"] = float(min_lns_cp_sat_time_limit_seconds)
        stats["lns_neighborhood_mode_effective"] = lns_effective_mode_last
        stats["lns_neighborhood_mode_requested"] = lns_neighborhood_mode
        stats["lns_poste_plus_one_top_days_k"] = int(lns_poste_plus_one_top_days_k)
        stats["lns_poste_plus_one_top_days_selected_sample"] = lns_poste_plus_one_top_days_selected_sample
        stats["lns_poste_plus_one_top_days_days_sample"] = lns_poste_plus_one_top_days_selected_sample
        stats["lns_history_truncated"] = bool(lns_history_truncated)
        stats["lns_history_max_items"] = int(lns_history_max_items)

        return LnsRunResult(
            best_solution=best_solution,
            lns_iterations=lns_iterations,
            lns_accept_count=lns_accept_count,
            lns_best_improvement_understaff=lns_best_improvement_understaff,
            lns_best_improvement_objective=lns_best_improvement_objective,
            lns_neighborhoods_tried=lns_neighborhoods_tried,
        )
