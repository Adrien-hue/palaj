from __future__ import annotations

from copy import deepcopy
import os
from typing import Any


class StatsCollector:
    SCHEMA_VERSION = 2
    DEFAULT_COMPACT_MAX_ITEMS = 20

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
        truncated_items = value[:max_items]
        field_name = alias or key
        container[key] = truncated_items
        container[f"{field_name}_truncated"] = total > max_items
        container[f"{field_name}_total"] = total

    @staticmethod
    def _filter_positive_understaff_days(coverage_stats: dict[str, Any], max_items: int) -> None:
        day_weights = coverage_stats.get("understaff_by_day_weighted")
        if not isinstance(day_weights, dict):
            return

        positive_days = [(str(day), int(weight)) for day, weight in day_weights.items() if weight > 0]
        positive_days.sort(key=lambda item: (-item[1], item[0]))
        selected = positive_days[:max_items]

        coverage_stats["understaff_by_day_weighted"] = {day: weight for day, weight in selected}
        coverage_stats["understaff_by_day_weighted_truncated"] = len(positive_days) > max_items
        coverage_stats["understaff_by_day_weighted_total"] = len(positive_days)

    def build_grouped_stats(self, flat: dict[str, Any]) -> dict[str, Any]:
        model_keys = {
            "num_variables",
            "num_constraints",
            "variable_count_method",
            "constraint_count_method",
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
            "combo_rejected_samples",
            "combo_allowed_samples",
            "missing_tranche_in_any_combo_sample",
            "missing_tranche_in_any_combo_count",
            "covered_tranche_ids_by_any_combo_count",
            "demanded_tranche_ids_count",
            "num_incompatible_pairs",
            "coverage_constraints_count",
            "demand_count",
            "demanded_pairs_count",
            "poste_count",
            "agent_count",
            "tranche_count",
        }
        coverage_keys = {
            "coverage_ratio",
            "coverage_ratio_weighted",
            "total_required_count",
            "total_required_count_weighted",
            "understaff_total",
            "understaff_total_weighted",
            "understaff_total_unweighted",
            "understaff_by_day_weighted",
            "top_understaff_days",
            "smoothing_term_components_count",
        }
        solution_quality_keys = {
            "nights_total",
            "nights_min",
            "nights_max",
            "workload_min",
            "workload_max",
            "workload_avg",
            "max_work_days",
            "min_work_days",
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
            "useless_work_total",
            "soft_violations",
        }

        grouped_lns = {k: v for k, v in flat.items() if k.startswith("lns_")}
        grouped_lns["iteration_history"] = flat.get("lns_iteration_history", [])

        return {
            "meta": {
                "schema_version": self.SCHEMA_VERSION,
                "verbosity": self.verbosity,
            },
            "timing": {
                "global": {
                    key: flat[key]
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
                    if key in flat
                },
                "phases": {
                    "phase1": {k: v for k, v in flat.items() if k.startswith("phase1_")},
                    "phase2": {k: v for k, v in flat.items() if k.startswith("phase2_")},
                    "lns": {k: v for k, v in flat.items() if k.startswith("lns_") and "time" in k},
                },
            },
            "model": {k: v for k, v in flat.items() if k in model_keys},
            "coverage": {k: v for k, v in flat.items() if k in coverage_keys},
            "objective": {
                key: flat[key]
                for key in ["objective_value", "score", "objective_terms", "dominance_ratios"]
                if key in flat
            },
            "solution_quality": {k: v for k, v in flat.items() if k in solution_quality_keys},
            "lns": grouped_lns,
            "cp_sat": {
                "cp_sat_params_effective": flat.get("cp_sat_params_effective"),
                "decision_strategy_enabled": flat.get("decision_strategy_enabled"),
                "decision_strategy_prioritized_vars_count": flat.get("decision_strategy_prioritized_vars_count"),
                "decision_strategy_day_scores_top": flat.get("decision_strategy_day_scores_top"),
                "symmetry_breaking_enabled": flat.get("symmetry_breaking_enabled"),
                "symmetry_constraints_count": flat.get("symmetry_constraints_count"),
                "phases": {
                    "phase1": {k: v for k, v in flat.items() if k.startswith("phase1_")},
                    "phase2": {k: v for k, v in flat.items() if k.startswith("phase2_")},
                },
            },
        }

    def apply_verbosity(self, grouped: dict[str, Any], verbosity: str) -> dict[str, Any]:
        result = deepcopy(grouped)
        result.setdefault("meta", {})["verbosity"] = verbosity
        if verbosity != "compact":
            return result

        max_items = self.DEFAULT_COMPACT_MAX_ITEMS

        lns_stats = result.get("lns", {})
        self._truncate_list_keep_type(lns_stats, "iteration_history", max_items)

        model_stats = result.get("model", {})
        for key in ["combo_rejected_samples", "combo_allowed_samples", "missing_tranche_in_any_combo_sample"]:
            self._truncate_list_keep_type(model_stats, key, max_items)

        coverage_stats = result.get("coverage", {})
        self._truncate_list_keep_type(coverage_stats, "top_understaff_days", max_items)
        self._filter_positive_understaff_days(coverage_stats, max_items)

        return result

    def finalize(self, flat: dict[str, Any]) -> dict[str, Any]:
        result = dict(flat)
        grouped = self.build_grouped_stats(result)
        result["stats"] = self.apply_verbosity(grouped, self.verbosity)
        result["result_stats_schema_version"] = self.SCHEMA_VERSION
        return result
