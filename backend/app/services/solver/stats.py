from __future__ import annotations

from copy import deepcopy
import os
from typing import Any

from backend.app.services.solver.constants import (
    DEFAULT_COMPACT_MAX_ITEMS as DEFAULT_COMPACT_MAX_ITEMS_CONST,
    RESULT_STATS_SCHEMA_VERSION,
    SOLVER_VERSION,
)


class StatsCollector:
    SCHEMA_VERSION = RESULT_STATS_SCHEMA_VERSION
    DEFAULT_COMPACT_MAX_ITEMS = DEFAULT_COMPACT_MAX_ITEMS_CONST

    def __init__(self, verbosity: str = "debug"):
        self.verbosity = verbosity if verbosity in {"compact", "debug"} else "debug"

    @classmethod
    def from_env(cls) -> "StatsCollector":
        raw = (os.getenv("PLANNING_STATS_VERBOSITY") or "").strip().lower()
        if raw:
            return cls(verbosity=raw)
        default_raw = (os.getenv("PLANNING_STATS_DEFAULT_VERBOSITY") or "debug").strip().lower()
        return cls(verbosity=default_raw)

    @staticmethod
    def _truncate_list_keep_type(container: dict[str, Any], key: str, max_items: int, *, alias: str | None = None) -> None:
        value = container.get(key)
        if not isinstance(value, list):
            return
        total = len(value)
        container[key] = value[:max_items]
        field_name = alias or key
        container[f"{field_name}_truncated"] = total > max_items
        container[f"{field_name}_total"] = total

    @staticmethod
    def _attach_list_meta(container: dict[str, Any], key: str, *, alias: str | None = None) -> None:
        value = container.get(key)
        if not isinstance(value, list):
            return
        field_name = alias or key
        container[f"{field_name}_truncated"] = False
        container[f"{field_name}_total"] = len(value)

    @staticmethod
    def _filter_positive_understaff_days(coverage_stats: dict[str, Any], max_items: int) -> None:
        day_weights = coverage_stats.get("understaff_by_day_weighted")
        if not isinstance(day_weights, dict):
            return
        positive_days = [(str(day), float(weight)) for day, weight in day_weights.items() if weight > 0]
        positive_days.sort(key=lambda item: (-item[1], item[0]))
        selected = positive_days[:max_items]
        coverage_stats["understaff_by_day_weighted"] = {day: weight for day, weight in selected}
        coverage_stats["understaff_by_day_weighted_truncated"] = len(positive_days) > max_items
        coverage_stats["understaff_by_day_weighted_total"] = len(positive_days)

    def build_grouped_stats(self, flat: dict[str, Any]) -> dict[str, Any]:
        model_keys = {
            "agent_count",
            "poste_count",
            "tranche_count",
            "demand_count",
            "demanded_pairs_count",
            "coverage_constraints_count",
            "num_combos_total",
            "num_combos_in_model",
            "num_combos_used_in_solution",
            "num_combos_effective",
            "y_variables_count",
            "combo_candidate_pairs_count",
            "combo_allowed_pairs_count",
            "combo_rejected_absence_count",
            "combo_rejected_not_qualified_count",
            "combo_rejected_qualification_date_count",
            "combo_rejected_unknown_daytype_forces_rest_count",
            "combo_rejected_other_count",
            "num_incompatible_pairs",
            "demanded_tranche_ids_count",
            "covered_tranche_ids_by_any_combo_count",
            "missing_tranche_in_any_combo_count",
            "variable_count_method",
            "constraint_count_method",
            "num_variables",
            "num_constraints",
            "combo_rejected_samples",
            "combo_allowed_samples",
            "missing_tranche_in_any_combo_sample",
        }
        coverage_keys = {
            "coverage_ratio",
            "total_required_count",
            "understaff_total",
            "understaff_total_weighted",
            "coverage_ratio_weighted",
            "smoothing_term_components_count",
            "top_understaff_days",
            "understaff_by_day_weighted",
        }
        objective_keys = {"objective_value", "score", "objective_terms", "dominance_ratios"}
        solution_quality_keys = {
            "soft_violations",
            "useless_work_total",
            "nights_total",
            "nights_min",
            "nights_max",
            "amplitude_cost_total",
            "stability_changes_total",
            "stability_changes_by_agent",
            "work_blocks_starts_total",
            "work_blocks_starts_by_agent",
            "rpdouble_soft_total",
            "rpdouble_soft_by_agent",
            "tranche_diversity_total",
            "tranche_diversity_by_agent",
            "understaff_smooth_weighted_sum",
            "workload_min",
            "workload_max",
            "workload_avg",
            "max_work_days",
            "min_work_days",
            "num_assignments",
        }

        lns_keys = {
            "lns_model_rebuild_wall_time_seconds_total",
            "lns_solve_wall_time_seconds_total",
            "lns_last_selected_poste_id",
            "lns_model_invalid",
            "lns_model_invalid_message",
            "lns_model_invalid_iteration_index",
            "lns_strict_improve",
            "lns_max_days_to_relax",
            "lns_iterations_time_budget_max",
            "lns_iterations_actual",
            "lns_avg_solve_wall_time_seconds_iter",
            "lns_min_solve_wall_time_seconds_iter",
            "lns_max_solve_wall_time_seconds_iter",
            "lns_solver_time_limit_seconds_applied",
            "lns_neighborhood_mode",
            "lns_neighborhood_mode_requested",
            "lns_neighborhood_mode_used_counts",
            "lns_selected_postes_last",
            "lns_relaxed_days_count_last",
            "lns_fixed_days_count_last",
            "lns_fixed_y_count_last",
            "lns_relaxed_y_count_last",
            "lns_fixed_vars_count_last",
            "lns_relaxed_vars_count_last",
            "lns_fixed_runs_count_last",
            "lns_relaxed_runs_count_last",
            "lns_iter_has_solution",
            "lns_iter_status_raw",
            "lns_iter_status_int",
            "lns_iter_objective_value",
            "lns_iter_understaff_total_unweighted",
            "lns_iter_validate_message_present",
            "lns_unknown_count_total",
            "lns_no_solution_count_total",
            "lns_fallback_triggered",
            "lns_fallback_reason",
            "lns_fallback_after_iterations",
            "lns_fallback_iteration_index",
            "lns_accept_count_at_fallback",
            "lns_last_accept_iteration_index",
            "lns_last_accept_t",
            "lns_early_stop_triggered",
            "lns_early_stop_reason",
            "lns_remaining_budget_seconds_at_stop",
            "lns_min_remaining_seconds_to_run_iter",
            "lns_iter_overhead_seconds",
            "lns_required_budget_seconds_to_start_iter",
            "lns_intended_iter_time_limit_seconds_last",
            "lns_iter_time_limit_seconds_effective_last",
            "lns_iter_time_limit_seconds_min",
            "lns_neighborhood_mode_effective",
            "lns_poste_plus_one_top_days_k",
            "lns_poste_plus_one_top_days_selected_sample",
            "lns_poste_plus_one_top_days_days_sample",
            "lns_history_truncated",
            "lns_history_max_items",
            "lns_enabled",
            "lns_iterations",
            "lns_total_wall_time_seconds",
            "lns_iter_time_seconds",
            "lns_best_improvement_understaff_unweighted",
            "lns_best_improvement_objective",
            "lns_best_understaff_total_unweighted",
            "lns_best_objective_value",
            "lns_accept_count",
            "lns_accept_count_total",
            "lns_neighborhoods_tried_by_poste",
        }

        cp_sat = {
            "cp_sat_params_effective": flat.get("cp_sat_params_effective", {}),
            "decision_strategy_enabled": flat.get("decision_strategy_enabled"),
            "decision_strategy_prioritized_vars_count": flat.get("decision_strategy_prioritized_vars_count"),
            "decision_strategy_day_scores_top": flat.get("decision_strategy_day_scores_top", []),
            "symmetry_breaking_enabled": flat.get("symmetry_breaking_enabled"),
            "symmetry_constraints_count": flat.get("symmetry_constraints_count"),
            "phases": {
                "phase1": {k: v for k, v in flat.items() if k.startswith("phase1_")},
                "phase2": {k: v for k, v in flat.items() if k.startswith("phase2_")},
            },
            "best_objective_over_time_points": flat.get("best_objective_over_time_points", []),
            "time_to_first_feasible_seconds": flat.get("time_to_first_feasible_seconds"),
        }

        return {
            "meta": {
                "verbosity": self.verbosity,
                "schema_version": self.SCHEMA_VERSION,
                "solver_version": SOLVER_VERSION,
            },
            "timing": {
                "global": {
                    key: flat.get(key)
                    for key in [
                        "time_limit_seconds",
                        "solver_max_time_seconds_applied",
                        "solve_wall_time_seconds",
                        "solve_time_seconds",
                        "model_build_wall_time_seconds",
                        "phase2_model_rebuild_wall_time_seconds",
                        "phase2_solve_wall_time_seconds",
                        "lns_model_rebuild_wall_time_seconds_total",
                        "lns_solve_wall_time_seconds_total",
                    ]
                }
            },
            "model": {k: flat.get(k) for k in model_keys},
            "coverage": {k: flat.get(k) for k in coverage_keys},
            "objective": {k: flat.get(k) for k in objective_keys},
            "solution_quality": {k: flat.get(k) for k in solution_quality_keys},
            "lns": {**{k: flat.get(k) for k in lns_keys}, "iteration_history": flat.get("lns_iteration_history", [])},
            "cp_sat": cp_sat,
        }

    def apply_verbosity(self, grouped: dict[str, Any], verbosity: str) -> dict[str, Any]:
        result = deepcopy(grouped)
        result.setdefault("meta", {})["verbosity"] = verbosity
        lns = result.get("lns", {})
        model = result.get("model", {})
        coverage = result.get("coverage", {})

        if verbosity != "compact":
            self._attach_list_meta(lns, "iteration_history")
            self._attach_list_meta(model, "combo_rejected_samples")
            self._attach_list_meta(model, "combo_allowed_samples")
            self._attach_list_meta(model, "missing_tranche_in_any_combo_sample")
            self._attach_list_meta(coverage, "top_understaff_days")
            return result

        max_items = self.DEFAULT_COMPACT_MAX_ITEMS
        self._truncate_list_keep_type(lns, "iteration_history", max_items)
        self._truncate_list_keep_type(model, "combo_rejected_samples", max_items)
        self._truncate_list_keep_type(model, "combo_allowed_samples", max_items)
        self._truncate_list_keep_type(model, "missing_tranche_in_any_combo_sample", max_items)
        self._truncate_list_keep_type(coverage, "top_understaff_days", max_items)
        self._filter_positive_understaff_days(coverage, max_items)
        return result

    def finalize(self, flat: dict[str, Any]) -> dict[str, Any]:
        grouped = self.build_grouped_stats(flat)
        return {
            "result_stats_schema_version": self.SCHEMA_VERSION,
            "stats": self.apply_verbosity(grouped, self.verbosity),
        }
