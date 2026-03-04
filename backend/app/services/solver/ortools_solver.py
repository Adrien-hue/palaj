from __future__ import annotations

from datetime import timedelta
import time

from ortools.sat.python import cp_model

from core.domain.enums.day_type import DayType

from .models import InfeasibleError, SolverAgentDay, SolverAssignment, SolverInput, SolverOutput, TimeoutError
from .lns_runner import LnsRunner
from .rh_combos import DayCombo, DayKind, DefaultRhComboRulesEngine, build_day_combos_for_poste, build_rest_compatibility
from .stats import StatsCollector


MIN_LNS_REMAINING_SECONDS_TO_RUN_ITER = 0.2
LNS_ITER_OVERHEAD_SECONDS = 0.05
MIN_LNS_CP_SAT_TIME_LIMIT_SECONDS = 0.2


class OrtoolsSolver:
    # Explicit coverage-priority order (strict):
    # weekday day > weekend day > weekday night > weekend night.
    W_UNDERSTAFF_WEEKDAY_DAY = 100
    W_UNDERSTAFF_WEEKEND_DAY = 20
    W_UNDERSTAFF_WEEKDAY_NIGHT = 10
    W_UNDERSTAFF_WEEKEND_NIGHT = 2

    W_COVER = 1_000_000
    W_NIGHTS_TOTAL = 10_000
    W_NIGHTS_SPREAD = 5_000
    W_FAIR_MINUTES_SPREAD = 1_000
    W_FAIR_DAYS_SPREAD = 500
    W_AMPLITUDE = 10
    W_USELESS_WORK = 50
    # Tie-breakers: intentionally far below coverage term to preserve strict coverage dominance.
    W_STABILITY_CHANGE = 20
    W_WORK_BLOCKS = 15
    W_RPDOUBLE_BONUS = 5
    W_TRANCHE_DIVERSITY = 5
    W_UNDERSTAFF_SMOOTH = 1

    GPT_DAY_TYPES = {
        DayType.WORKING.value,
        DayType.ZCOT.value,
        DayType.LEAVE.value,
        DayType.ABSENT.value,
    }
    REAL_WORK_DAY_TYPES_CONTEXT = {
        DayType.WORKING.value,
        DayType.ZCOT.value,
    }
    RPDOUBLE_OFF_RULE = "rest_only"
    RPDOUBLE_OFF_DAY_TYPES = {DayType.REST.value}
    MAX_LNS_HISTORY_ITEMS = 200

    @staticmethod
    def _time_to_minutes(value) -> int:
        return (value.hour * 60) + value.minute

    @classmethod
    def _tranche_duration_minutes(cls, tranche) -> int:
        start = cls._time_to_minutes(tranche.heure_debut)
        end = cls._time_to_minutes(tranche.heure_fin)
        if end <= start:
            end += 1440
        return end - start

    @staticmethod
    def _is_night_tranche(tranche) -> bool:
        return tranche is not None and (tranche.heure_debut.hour >= 17)

    @classmethod
    def _understaff_priority_weight(cls, *, is_weekday: bool, is_night: bool) -> int:
        if is_weekday and not is_night:
            return cls.W_UNDERSTAFF_WEEKDAY_DAY
        if (not is_weekday) and (not is_night):
            return cls.W_UNDERSTAFF_WEEKEND_DAY
        if is_weekday and is_night:
            return cls.W_UNDERSTAFF_WEEKDAY_NIGHT
        return cls.W_UNDERSTAFF_WEEKEND_NIGHT

    @classmethod
    def _understaff_priority_weight_for_demand(cls, *, day_date, tranche) -> int:
        return cls._understaff_priority_weight(
            is_weekday=(day_date.weekday() < 5),
            is_night=cls._is_night_tranche(tranche),
        )

    @staticmethod
    def _is_rest_combo(combo: DayCombo) -> bool:
        return combo.day_kind == DayKind.REST

    @staticmethod
    def _is_work_combo(combo: DayCombo) -> bool:
        return combo.day_kind in {DayKind.WORK, DayKind.ZCOT, DayKind.LEAVE, DayKind.ABSENT}

    @staticmethod
    def _is_off_for_rpdouble_combo(combo: DayCombo) -> bool:
        return combo.day_kind == DayKind.REST

    @staticmethod
    def _combo_tranches(combo: DayCombo) -> tuple[int, ...]:
        return combo.tranche_ids

    @classmethod
    def _combo_dominant_tranche_id(cls, combo: DayCombo, tranche_duration_by_id: dict[int, int]) -> int | None:
        if not combo.tranche_ids:
            return None
        return min(
            combo.tranche_ids,
            key=lambda tranche_id: (-tranche_duration_by_id.get(tranche_id, 0), tranche_id),
        )

    def generate(self, solver_input: SolverInput) -> SolverOutput:
        stats_collector = StatsCollector.from_env()
        solve_started_at = time.monotonic()
        model = cp_model.CpModel()
        num_constraints = 0
        num_variables = 0

        ordered_agent_ids = sorted(solver_input.agent_ids)
        dates: list = []
        cursor = solver_input.start_date
        while cursor <= solver_input.end_date:
            dates.append(cursor)
            cursor += timedelta(days=1)
        date_to_index = {d: i for i, d in enumerate(dates)}
        date_to_period_index = {d: i for i, d in enumerate(dates)}

        apply_gpt_rules = bool(solver_input.gpt_context_days)
        context_days = list(solver_input.gpt_context_days) if apply_gpt_rules else list(dates)
        ctx_date_to_index = {d: i for i, d in enumerate(context_days)}
        in_window_ctx_indices = {ctx_date_to_index[d] for d in dates if d in ctx_date_to_index}

        qual_posts = {agent_id: set(postes) for agent_id, postes in solver_input.qualified_postes_by_agent.items()}
        qual_date = solver_input.qualification_date_by_agent_poste

        demanded_tranche_ids_by_date_idx: dict[int, set[int]] = {}
        for demand in solver_input.coverage_demands:
            di = date_to_index[demand.day_date]
            demanded_tranche_ids_by_date_idx.setdefault(di, set()).add(demand.tranche_id)
        demanded_pairs_count = sum(len(tranche_ids) for tranche_ids in demanded_tranche_ids_by_date_idx.values())
        demanded_day_idx_set = set(demanded_tranche_ids_by_date_idx)

        tranche_duration_by_id = {tranche.id: self._tranche_duration_minutes(tranche) for tranche in solver_input.tranches}
        tranche_by_id = {tranche.id: tranche for tranche in solver_input.tranches}
        total_required_work_minutes = sum(
            max(0, demand.required_count) * tranche_duration_by_id.get(demand.tranche_id, 0)
            for demand in solver_input.coverage_demands
        )

        tranches_by_poste: dict[int, list] = {}
        for tranche in solver_input.tranches:
            tranches_by_poste.setdefault(tranche.poste_id, []).append(tranche)

        rh_engine = DefaultRhComboRulesEngine()
        rest_combo = DayCombo(
            id=0,
            poste_id=None,
            tranche_ids=(),
            start_min=None,
            end_min=None,
            work_minutes=0,
            amplitude_minutes=0,
            involves_night=False,
            day_kind=DayKind.REST,
        )
        combos: list[DayCombo] = [rest_combo]
        next_combo_id = 1
        for poste_id in sorted(tranches_by_poste):
            poste_combos = build_day_combos_for_poste(tranches=tranches_by_poste[poste_id], rh_engine=rh_engine)
            for combo in poste_combos:
                combos.append(
                    DayCombo(
                        id=next_combo_id,
                        poste_id=combo.poste_id,
                        tranche_ids=combo.tranche_ids,
                        start_min=combo.start_min,
                        end_min=combo.end_min,
                        work_minutes=combo.work_minutes,
                        amplitude_minutes=combo.amplitude_minutes,
                        involves_night=combo.involves_night,
                        day_kind=combo.day_kind,
                    )
                )
                next_combo_id += 1

        combo_by_id = {combo.id: combo for combo in combos}
        combo_main_tranche_id = {
            combo.id: self._combo_dominant_tranche_id(combo, tranche_duration_by_id)
            for combo in combos
        }
        sorted_combos = sorted(combos, key=lambda combo: ((combo.poste_id if combo.poste_id is not None else -1), combo.id))
        sorted_work_combos = [combo for combo in sorted_combos if self._is_work_combo(combo)]
        combo_ids_by_poste: dict[int, list[int]] = {}
        for combo in combos:
            if combo.poste_id is not None:
                combo_ids_by_poste.setdefault(combo.poste_id, []).append(combo.id)

        compatible_pairs = build_rest_compatibility(combos=combos, rh_engine=rh_engine)
        incompatible_pairs = {(c1, c2) for c1 in combo_by_id for c2 in combo_by_id if (c1, c2) not in compatible_pairs}
        num_combos_total = len(combos)
        num_incompatible_pairs = len(incompatible_pairs)
        gpt_ctx_days_count = len(context_days) if apply_gpt_rules else 0
        rpdouble_off_rule = self.RPDOUBLE_OFF_RULE if apply_gpt_rules else None
        total_days = len(dates)
        agent_count = len(ordered_agent_ids)
        avg_required_minutes_per_day = (total_required_work_minutes / total_days) if total_days else 0.0
        avg_required_minutes_per_agent_per_day = (
            total_required_work_minutes / (total_days * agent_count)
            if total_days and agent_count
            else 0.0
        )
        total_required_count = sum(max(0, demand.required_count) for demand in solver_input.coverage_demands)
        total_required_weighted = sum(
            self._understaff_priority_weight_for_demand(day_date=demand.day_date, tranche=tranche_by_id.get(demand.tranche_id))
            * max(0, demand.required_count)
            for demand in solver_input.coverage_demands
        )
        time_limit_seconds = float(solver_input.time_limit_seconds or 0.0)
        profile = (solver_input.quality_profile or "balanced").lower()

        stats = {
            "solver_status": None,
            "solver_status_raw": None,
            "normalized_solver_status": None,
            "is_timeout": False,
            "time_limit_reached": False,
            "timeout_detection_method": "status_feasible_or_walltime_95pct",
            "time_limit_seconds": time_limit_seconds,
            "solver_max_time_seconds_applied": 0.0,
            "solve_wall_time_seconds": 0.0,
            "solver_status_int": None,
            "solve_time_seconds": 0.0,
            "coverage_ratio": 0.0,
            "total_required_count": total_required_count,
            "total_required_weighted": total_required_weighted,
            "understaff_total": 0,
            "understaff_total_weighted": 0,
            "coverage_ratio_weighted": 0.0,
            "soft_violations": 0,
            "agent_count": agent_count,
            "poste_count": len(solver_input.poste_ids),
            "tranche_count": len(solver_input.tranches),
            "demand_count": len(solver_input.coverage_demands),
            "demanded_pairs_count": demanded_pairs_count,
            "coverage_constraints_count": 0,
            "num_combos_total": num_combos_total,
            "num_combos_in_model": 0,
            "num_combos_used_in_solution": None,
            "num_combos_effective": 0,
            "y_variables_count": 0,
            "combo_candidate_pairs_count": 0,
            "combo_allowed_pairs_count": 0,
            "combo_rejected_absence_count": 0,
            "combo_rejected_not_qualified_count": 0,
            "combo_rejected_qualification_date_count": 0,
            "combo_rejected_unknown_daytype_forces_rest_count": 0,
            "combo_rejected_other_count": 0,
            "combo_rejected_samples": [],
            "combo_allowed_samples": [],
            "num_incompatible_pairs": num_incompatible_pairs,
            "num_rest_constraints": 0,
            "gpt_ctx_days_count": gpt_ctx_days_count,
            "gpt_window_days_count": len(dates) if apply_gpt_rules else 0,
            "worked_ctx_window_fixed_days_count_by_agent": {},
            "runs_selected_total": 0,
            "runs_selected_by_agent": {},
            "runs_candidate_count_by_agent": {},
            "max_possible_runs_by_agent": {},
            "daily_choice_mode": "exactly_one",
            "rest_combo_count_in_model": 0,
            "rest_combo_allowed_count_sample": [],
            "has_rest_choice_each_day_in_window_by_agent": {},
            "has_work_choice_each_day_in_window_by_agent": {},
            "worked_window_forced_zero_by_agent": {},
            "run_feasible_candidate_count_by_agent": {},
            "coverage_active": False,
            "can_cover_any_demand_in_window": False,
            "rpdouble_off_rule": rpdouble_off_rule,
            "total_required_work_minutes": total_required_work_minutes,
            "avg_required_minutes_per_day": avg_required_minutes_per_day,
            "avg_required_minutes_per_agent_per_day": avg_required_minutes_per_agent_per_day,
            "gpt_max_avg_minutes_per_day_if_6": 480,
            "demanded_tranche_ids_count": 0,
            "covered_tranche_ids_by_any_combo_count": 0,
            "missing_tranche_in_any_combo_count": 0,
            "missing_tranche_in_any_combo_sample": [],
            # Heuristic estimation from demand volume; useful diagnostic signal, not a proof of feasibility.
            "required_minutes_estimate_method": "sum(tranche_duration_minutes * required_count) over coverage_demands",
            "total_required_work_minutes_estimate": total_required_work_minutes,
            "avg_required_minutes_per_agent_per_day_estimate": avg_required_minutes_per_agent_per_day,
            "variable_count_method": "internal_counter",
            "constraint_count_method": "internal_counter",
            "num_variables": 0,
            "num_constraints": 0,
            "demanded_days_count": len(demanded_day_idx_set),
            "total_days_count": total_days,
            "useless_work_total": 0,
            "nights_total": 0,
            "nights_min": 0,
            "nights_max": 0,
            "amplitude_cost_total": 0,
            "stability_changes_total": 0,
            "stability_changes_by_agent": {},
            "work_blocks_starts_total": 0,
            "work_blocks_starts_by_agent": {},
            "rpdouble_soft_total": 0,
            "rpdouble_soft_by_agent": {},
            "tranche_diversity_total": 0,
            "tranche_diversity_by_agent": {},
            "understaff_smooth_weighted_sum": 0,
            "dominance_ratios": {
                "cost_one_understaff_weekday_day": 0,
                "cost_one_understaff_weekend_day": 0,
                "cost_one_understaff_weekday_night": 0,
                "cost_one_understaff_weekend_night": 0,
                "stability_changes_max": 0,
                "work_block_starts_max": 0,
                "rpdouble_soft_max": 0,
                "tranche_diversity_max": 0,
                "understaff_smooth_max": 0,
                "max_cost_stability": 0,
                "max_cost_blocks": 0,
                "max_cost_rpdouble": 0,
                "max_cost_diversity": 0,
                "max_cost_smoothing": 0,
                "max_cost_all_tiebreakers": 0,
                "ratio_all_tiebreakers_vs_one_understaff_weekday_day": 0.0,
                "ratio_all_tiebreakers_vs_one_understaff_weekend_day": 0.0,
                "ratio_all_tiebreakers_vs_one_understaff_weekday_night": 0.0,
                "ratio_all_tiebreakers_vs_one_understaff_weekend_night": 0.0,
            },
            "model_build_wall_time_seconds": 0.0,
            "phase2_model_rebuild_wall_time_seconds": 0.0,
            "phase2_reused_model": True,
            "phase2_solve_wall_time_seconds": 0.0,
            "lns_model_rebuild_wall_time_seconds_total": 0.0,
            "lns_solve_wall_time_seconds_total": 0.0,
            "lns_iteration_history": [],
            "lns_last_selected_poste_id": None,
            "lns_model_invalid": False,
            "lns_model_invalid_message": None,
            "lns_model_invalid_iteration_index": None,
            "lns_strict_improve": True,
            "lns_max_days_to_relax": 14,
            "min_lns_seconds": 0.0,
            "lns_iterations_time_budget_max": 0,
            "lns_iterations_actual": 0,
            "lns_avg_solve_wall_time_seconds_iter": 0.0,
            "lns_min_solve_wall_time_seconds_iter": 0.0,
            "lns_max_solve_wall_time_seconds_iter": 0.0,
            "lns_solver_time_limit_seconds_applied": 0.0,
            "lns_neighborhood_mode": "poste_only",
            "lns_neighborhood_mode_requested": "poste_only",
            "lns_neighborhood_mode_used_counts": {},
            "lns_selected_postes_last": [],
            "lns_relaxed_days_count_last": 0,
            "lns_fixed_days_count_last": 0,
            "lns_fixed_y_count_last": 0,
            "lns_relaxed_y_count_last": 0,
            "lns_fixed_vars_count_last": 0,
            "lns_relaxed_vars_count_last": 0,
            "lns_fixed_runs_count_last": 0,
            "lns_relaxed_runs_count_last": 0,
            "lns_iter_has_solution": False,
            "lns_iter_status_raw": None,
            "lns_iter_status_int": None,
            "lns_iter_objective_value": None,
            "lns_iter_understaff_total_unweighted": None,
            "lns_iter_validate_message_present": False,
            "lns_unknown_count_total": 0,
            "lns_no_solution_count_total": 0,
            "lns_fallback_triggered": False,
            "lns_fallback_reason": None,
            "lns_fallback_after_iterations": None,
            "lns_fallback_iteration_index": None,
            "lns_accept_count_at_fallback": 0,
            "lns_last_accept_iteration_index": None,
            "lns_last_accept_t": None,
            "lns_early_stop_triggered": False,
            "lns_early_stop_reason": None,
            "lns_remaining_budget_seconds_at_stop": None,
            "lns_min_remaining_seconds_to_run_iter": float(MIN_LNS_REMAINING_SECONDS_TO_RUN_ITER),
            "lns_iter_overhead_seconds": float(LNS_ITER_OVERHEAD_SECONDS),
            "lns_required_budget_seconds_to_start_iter": None,
            "lns_intended_iter_time_limit_seconds_last": None,
            "lns_iter_time_limit_seconds_effective_last": None,
            "lns_iter_time_limit_seconds_min": float(MIN_LNS_CP_SAT_TIME_LIMIT_SECONDS),
            "lns_neighborhood_mode_effective": None,
            "lns_poste_plus_one_top_days_k": 0,
            "lns_poste_plus_one_top_days_selected_sample": [],
            "lns_poste_plus_one_top_days_days_sample": [],
            "lns_history_truncated": False,
            "lns_history_max_items": int(self.MAX_LNS_HISTORY_ITEMS),
            "cp_sat_params_effective": {},
            "decision_strategy_enabled": False,
            "decision_strategy_prioritized_vars_count": 0,
            "decision_strategy_day_scores_top": [],
            "symmetry_breaking_enabled": False,
            "symmetry_constraints_count": 0,
            "objective_terms": {
                "understaff_weighted": 0,
                "understaff_smooth_weighted": 0,
                "nights_total": 0,
                "nights_spread": 0,
                "fair_minutes_spread": 0,
                "fair_days_spread": 0,
                "amplitude_cost": 0,
                "useless_work": 0,
                "stability_changes": 0,
                "work_blocks_starts": 0,
                "rpdouble_soft_bonus": 0,
                "tranche_diversity_bonus": 0,
            },
        }

        y: dict[tuple[int, int, int], cp_model.IntVar] = {}
        vars_by_agent_day: dict[tuple[int, int], list[cp_model.IntVar]] = {}
        vars_by_demand: dict[tuple[int, int], list[cp_model.IntVar]] = {}

        covered_tranche_ids_by_any_combo = {
            tranche_id
            for combo in combos
            if combo.tranche_ids
            for tranche_id in combo.tranche_ids
        }
        demanded_tranche_ids = {demand.tranche_id for demand in solver_input.coverage_demands}
        missing_tranche_ids = demanded_tranche_ids - covered_tranche_ids_by_any_combo
        stats["demanded_tranche_ids_count"] = len(demanded_tranche_ids)
        stats["covered_tranche_ids_by_any_combo_count"] = len(covered_tranche_ids_by_any_combo)
        stats["missing_tranche_in_any_combo_count"] = len(missing_tranche_ids)
        stats["missing_tranche_in_any_combo_sample"] = sorted(missing_tranche_ids)[:10]

        # Rough upper bounds for objective dominance observability.
        cost_one_understaff_weekday_day = self.W_COVER * self.W_UNDERSTAFF_WEEKDAY_DAY
        cost_one_understaff_weekend_day = self.W_COVER * self.W_UNDERSTAFF_WEEKEND_DAY
        cost_one_understaff_weekday_night = self.W_COVER * self.W_UNDERSTAFF_WEEKDAY_NIGHT
        cost_one_understaff_weekend_night = self.W_COVER * self.W_UNDERSTAFF_WEEKEND_NIGHT
        stability_changes_max = agent_count * max(0, total_days - 1)
        work_block_starts_max = agent_count * total_days
        rpdouble_soft_max = agent_count * max(0, total_days - 1)
        eligible_tranche_ids_by_agent = {
            agent_id: {
                combo_main_tranche_id[combo_id]
                for combo_id in combo_by_id
                if combo_main_tranche_id[combo_id] is not None and combo_by_id[combo_id].poste_id in qual_posts.get(agent_id, set())
            }
            for agent_id in ordered_agent_ids
        }
        tranche_diversity_max = sum(len(v) for v in eligible_tranche_ids_by_agent.values())
        understaff_smooth_max = sum(
            self._understaff_priority_weight_for_demand(day_date=demand.day_date, tranche=tranche_by_id.get(demand.tranche_id))
            * (max(0, demand.required_count) ** 2)
            for demand in solver_input.coverage_demands
        )
        max_cost_stability = self.W_STABILITY_CHANGE * stability_changes_max
        max_cost_blocks = self.W_WORK_BLOCKS * work_block_starts_max
        max_cost_rpdouble = self.W_RPDOUBLE_BONUS * rpdouble_soft_max
        max_cost_diversity = self.W_TRANCHE_DIVERSITY * tranche_diversity_max
        max_cost_smoothing = self.W_UNDERSTAFF_SMOOTH * understaff_smooth_max
        max_cost_all_tiebreakers = (
            abs(max_cost_stability)
            + abs(max_cost_blocks)
            + abs(max_cost_rpdouble)
            + abs(max_cost_diversity)
            + abs(max_cost_smoothing)
        )
        stats["dominance_ratios"] = {
            "cost_one_understaff_weekday_day": cost_one_understaff_weekday_day,
            "cost_one_understaff_weekend_day": cost_one_understaff_weekend_day,
            "cost_one_understaff_weekday_night": cost_one_understaff_weekday_night,
            "cost_one_understaff_weekend_night": cost_one_understaff_weekend_night,
            "stability_changes_max": stability_changes_max,
            "work_block_starts_max": work_block_starts_max,
            "rpdouble_soft_max": rpdouble_soft_max,
            "tranche_diversity_max": tranche_diversity_max,
            "understaff_smooth_max": understaff_smooth_max,
            "max_cost_stability": max_cost_stability,
            "max_cost_blocks": max_cost_blocks,
            "max_cost_rpdouble": max_cost_rpdouble,
            "max_cost_diversity": max_cost_diversity,
            "max_cost_smoothing": max_cost_smoothing,
            "max_cost_all_tiebreakers": max_cost_all_tiebreakers,
            "ratio_all_tiebreakers_vs_one_understaff_weekday_day": (max_cost_all_tiebreakers / cost_one_understaff_weekday_day) if cost_one_understaff_weekday_day else 0.0,
            "ratio_all_tiebreakers_vs_one_understaff_weekend_day": (max_cost_all_tiebreakers / cost_one_understaff_weekend_day) if cost_one_understaff_weekend_day else 0.0,
            "ratio_all_tiebreakers_vs_one_understaff_weekday_night": (max_cost_all_tiebreakers / cost_one_understaff_weekday_night) if cost_one_understaff_weekday_night else 0.0,
            "ratio_all_tiebreakers_vs_one_understaff_weekend_night": (max_cost_all_tiebreakers / cost_one_understaff_weekend_night) if cost_one_understaff_weekend_night else 0.0,
        }
        if missing_tranche_ids:
            stats["solver_status"] = "INFEASIBLE"
            stats["solver_status_raw"] = "PRECHECK_INFEASIBLE"
            stats["normalized_solver_status"] = "INFEASIBLE"
            stats["is_timeout"] = False
            raise InfeasibleError("infeasible", stats=stats_collector.finalize(stats))

        combo_candidate_pairs_count = 0
        combo_allowed_pairs_count = 0
        combo_rejected_absence_count = 0
        combo_rejected_not_qualified_count = 0
        combo_rejected_qualification_date_count = 0
        combo_rejected_unknown_daytype_forces_rest_count = 0
        combo_rejected_other_count = 0
        combo_rejected_samples: list[dict] = []
        combo_allowed_samples: list[dict] = []
        y_variables_count = 0
        combo_ids_in_model: set[int] = set()

        def _append_sample(samples: list[dict], *, agent_id: int, day_date, combo_id: int, poste_id: int | None, reason: str) -> None:
            if len(samples) >= 10:
                return
            samples.append(
                {
                    "agent_id": agent_id,
                    "day_date": day_date.isoformat(),
                    "combo_id": combo_id,
                    "poste_id": poste_id,
                    "reason": reason,
                }
            )

        for agent_id in ordered_agent_ids:
            for di, day_date in enumerate(dates):
                is_absent = (agent_id, day_date) in solver_input.absences
                if is_absent:
                    var = model.NewBoolVar(f"y_a{agent_id}_d{di}_c0")
                    num_variables += 1
                    y_variables_count += 1
                    y[(agent_id, di, 0)] = var
                    combo_ids_in_model.add(0)
                    vars_by_agent_day.setdefault((agent_id, di), []).append(var)
                    model.Add(var == 1)
                    num_constraints += 1
                else:
                    var = model.NewBoolVar(f"y_a{agent_id}_d{di}_c0")
                    num_variables += 1
                    y_variables_count += 1
                    y[(agent_id, di, 0)] = var
                    combo_ids_in_model.add(0)
                    vars_by_agent_day.setdefault((agent_id, di), []).append(var)

                for combo in sorted_work_combos:
                    combo_candidate_pairs_count += 1
                    combo_id = combo.id
                    reason = None
                    if is_absent:
                        combo_rejected_absence_count += 1
                        reason = "absence"
                    elif combo.poste_id not in qual_posts.get(agent_id, set()):
                        combo_rejected_not_qualified_count += 1
                        reason = "not_qualified"
                    else:
                        min_qual_date = qual_date.get((agent_id, combo.poste_id))
                        if min_qual_date is not None and day_date < min_qual_date:
                            combo_rejected_qualification_date_count += 1
                            reason = "qualification_date"

                    if reason is not None:
                        _append_sample(
                            combo_rejected_samples,
                            agent_id=agent_id,
                            day_date=day_date,
                            combo_id=combo_id,
                            poste_id=combo.poste_id,
                            reason=reason,
                        )
                        continue

                    combo_allowed_pairs_count += 1
                    _append_sample(
                        combo_allowed_samples,
                        agent_id=agent_id,
                        day_date=day_date,
                        combo_id=combo_id,
                        poste_id=combo.poste_id,
                        reason="allowed",
                    )
                    var = model.NewBoolVar(f"y_a{agent_id}_d{di}_c{combo_id}")
                    num_variables += 1
                    y_variables_count += 1
                    y[(agent_id, di, combo_id)] = var
                    combo_ids_in_model.add(combo_id)
                    vars_by_agent_day.setdefault((agent_id, di), []).append(var)
                    for tranche_id in combo.tranche_ids:
                        vars_by_demand.setdefault((di, tranche_id), []).append(var)

        stats["combo_candidate_pairs_count"] = combo_candidate_pairs_count
        stats["combo_allowed_pairs_count"] = combo_allowed_pairs_count
        stats["combo_rejected_absence_count"] = combo_rejected_absence_count
        stats["combo_rejected_not_qualified_count"] = combo_rejected_not_qualified_count
        stats["combo_rejected_qualification_date_count"] = combo_rejected_qualification_date_count
        stats["combo_rejected_unknown_daytype_forces_rest_count"] = combo_rejected_unknown_daytype_forces_rest_count
        stats["combo_rejected_other_count"] = combo_rejected_other_count
        stats["combo_rejected_samples"] = combo_rejected_samples
        stats["combo_allowed_samples"] = combo_allowed_samples
        stats["y_variables_count"] = y_variables_count
        stats["num_combos_in_model"] = len(combo_ids_in_model)
        stats["num_combos_effective"] = stats["num_combos_in_model"]

        for agent_id in ordered_agent_ids:
            for di in range(len(dates)):
                day_vars = vars_by_agent_day.get((agent_id, di), [])
                if day_vars:
                    model.Add(sum(day_vars) == 1)
                    num_constraints += 1

        daily_choice_mode = "exactly_one"
        rest_combo_ids = [combo.id for combo in combos if combo.day_kind == DayKind.REST]
        stats["daily_choice_mode"] = daily_choice_mode
        stats["rest_combo_count_in_model"] = len(rest_combo_ids)

        has_rest_choice_each_day_in_window_by_agent: dict[int, bool] = {}
        has_work_choice_each_day_in_window_by_agent: dict[int, bool] = {}
        worked_window_forced_zero_by_agent: dict[int, bool] = {}
        rest_combo_allowed_count_sample: list[dict[str, int]] = []

        for agent_id in ordered_agent_ids:
            has_rest_each_day = True
            has_work_each_day = True
            for di in range(len(dates)):
                day_combo_ids = [c for (a, d, c) in y if a == agent_id and d == di]
                has_work_today = any(self._is_work_combo(combo_by_id[cid]) for cid in day_combo_ids)
                if not has_work_today:
                    has_work_each_day = False

                if daily_choice_mode == "at_most_one":
                    has_rest_today = True
                    rest_count = 0
                else:
                    rest_ids_today = [cid for cid in day_combo_ids if combo_by_id[cid].day_kind == DayKind.REST]
                    rest_count = len(rest_ids_today)
                    has_rest_today = rest_count > 0
                if not has_rest_today:
                    has_rest_each_day = False

                if len(rest_combo_allowed_count_sample) < 10:
                    rest_combo_allowed_count_sample.append({"agent_id": agent_id, "day_index": di, "rest_choices": rest_count})

            has_rest_choice_each_day_in_window_by_agent[agent_id] = has_rest_each_day
            has_work_choice_each_day_in_window_by_agent[agent_id] = has_work_each_day
            worked_window_forced_zero_by_agent[agent_id] = not has_work_each_day

        stats["rest_combo_allowed_count_sample"] = rest_combo_allowed_count_sample
        stats["has_rest_choice_each_day_in_window_by_agent"] = has_rest_choice_each_day_in_window_by_agent
        stats["has_work_choice_each_day_in_window_by_agent"] = has_work_choice_each_day_in_window_by_agent
        stats["worked_window_forced_zero_by_agent"] = worked_window_forced_zero_by_agent

        coverage_constraints_count = 0
        understaff_vars: list[cp_model.IntVar] = []
        weighted_understaff_terms: list[cp_model.LinearExprT] = []
        weighted_understaff_smooth_terms: list[cp_model.LinearExprT] = []
        demand_records: list[dict[str, object]] = []
        for demand in solver_input.coverage_demands:
            di = date_to_index[demand.day_date]
            demand_vars = vars_by_demand.get((di, demand.tranche_id), [])
            covered = model.NewIntVar(0, demand.required_count, f"covered_d{di}_t{demand.tranche_id}")
            num_variables += 1
            model.Add(covered == sum(demand_vars))
            num_constraints += 1
            model.Add(covered <= demand.required_count)
            num_constraints += 1

            understaff = model.NewIntVar(0, demand.required_count, f"understaff_d{di}_t{demand.tranche_id}")
            num_variables += 1
            model.Add(understaff == demand.required_count - covered)
            num_constraints += 1
            understaff_vars.append(understaff)
            tranche = tranche_by_id.get(demand.tranche_id)
            demand_weight = self._understaff_priority_weight_for_demand(day_date=demand.day_date, tranche=tranche)
            weighted_understaff_terms.append(demand_weight * understaff)

            understaff_sq = model.NewIntVar(0, demand.required_count * demand.required_count, f"understaff_sq_d{di}_t{demand.tranche_id}")
            num_variables += 1
            model.AddMultiplicationEquality(understaff_sq, [understaff, understaff])
            num_constraints += 1
            weighted_understaff_smooth_terms.append(demand_weight * understaff_sq)
            demand_poste_id = demand.poste_id if demand.poste_id is not None else tranche_by_id.get(demand.tranche_id).poste_id
            demand_records.append({"day_date": demand.day_date, "day_index": di, "tranche_id": demand.tranche_id, "poste_id": int(demand_poste_id), "understaff_var": understaff, "weight": demand_weight})
            coverage_constraints_count += 1

        stats["coverage_active"] = bool(coverage_constraints_count > 0 and demanded_pairs_count > 0)
        stats["can_cover_any_demand_in_window"] = any(
            bool(vars_by_demand.get((date_to_index[demand.day_date], demand.tranche_id), []))
            for demand in solver_input.coverage_demands
            if demand.day_date in date_to_index
        )

        rest_constraints_count = 0
        for agent_id in ordered_agent_ids:
            for di in range(1, len(dates)):
                for c1, c2 in incompatible_pairs:
                    prev_var = y.get((agent_id, di - 1, c1))
                    curr_var = y.get((agent_id, di, c2))
                    if prev_var is None or curr_var is None:
                        continue
                    model.Add(prev_var + curr_var <= 1)
                    num_constraints += 1
                    rest_constraints_count += 1

        run_vars: dict[tuple[int, int, int], cp_model.IntVar] = {}
        runs_candidate_count_by_agent: dict[int, int] = {agent_id: 0 for agent_id in ordered_agent_ids}
        if apply_gpt_rules:
            worked_ctx: dict[tuple[int, int], cp_model.IntVar | int] = {}
            minutes_ctx: dict[tuple[int, int], cp_model.IntVar | int] = {}
            off_ctx: dict[tuple[int, int], cp_model.IntVar | int] = {}
            worked_ctx_window_fixed_days_count_by_agent: dict[int, int] = {agent_id: 0 for agent_id in ordered_agent_ids}

            def is_in_window(idx: int) -> bool:
                return idx in in_window_ctx_indices

            for agent_id in ordered_agent_ids:
                for ci, day_date in enumerate(context_days):
                    key = (agent_id, day_date)
                    day_type_ctx = solver_input.existing_day_type_by_agent_day_ctx.get(key, DayType.REST.value)
                    if not is_in_window(ci):
                        if day_type_ctx == DayType.REST.value:
                            worked_ctx[(agent_id, ci)] = 0
                            minutes_ctx[(agent_id, ci)] = 0
                            off_ctx[(agent_id, ci)] = 1
                        elif day_type_ctx in {DayType.ZCOT.value, DayType.LEAVE.value, DayType.ABSENT.value}:
                            worked_ctx[(agent_id, ci)] = 1
                            minutes_ctx[(agent_id, ci)] = 0
                            off_ctx[(agent_id, ci)] = 0
                        else:
                            worked_ctx[(agent_id, ci)] = 1
                            minutes_ctx[(agent_id, ci)] = solver_input.existing_work_minutes_by_agent_day_ctx.get(key, 0)
                            off_ctx[(agent_id, ci)] = 0
                        continue

                    di = date_to_period_index[day_date]
                    work_terms = [
                        y[(agent_id, di, combo_id)]
                        for combo_id in combo_by_id
                        if (agent_id, di, combo_id) in y and self._is_work_combo(combo_by_id[combo_id])
                    ]
                    worked_day = model.NewBoolVar(f"worked_ctx_a{agent_id}_c{ci}")
                    num_variables += 1
                    if work_terms:
                        model.Add(worked_day == sum(work_terms))
                    else:
                        model.Add(worked_day == 0)
                    num_constraints += 1
                    worked_ctx[(agent_id, ci)] = worked_day

                    work_minutes = model.NewIntVar(0, 6000, f"minutes_ctx_a{agent_id}_c{ci}")
                    num_variables += 1
                    model.Add(
                        work_minutes
                        == sum(
                            y[(agent_id, di, combo_id)] * combo_by_id[combo_id].work_minutes
                            for combo_id in combo_by_id
                            if (agent_id, di, combo_id) in y
                        )
                    )
                    num_constraints += 1
                    minutes_ctx[(agent_id, ci)] = work_minutes

                    off_terms = [
                        y[(agent_id, di, combo_id)]
                        for combo_id in combo_by_id
                        if (agent_id, di, combo_id) in y and self._is_off_for_rpdouble_combo(combo_by_id[combo_id])
                    ]
                    off_day = model.NewBoolVar(f"off_ctx_a{agent_id}_c{ci}")
                    num_variables += 1
                    if off_terms:
                        model.Add(off_day == sum(off_terms))
                    else:
                        model.Add(off_day == 0)
                    num_constraints += 1
                    off_ctx[(agent_id, ci)] = off_day

            N_ctx = len(context_days)
            for agent_id in ordered_agent_ids:
                for s in range(N_ctx):
                    for e in range(s, min(N_ctx, s + 6)):
                        L = e - s + 1
                        if L < 3:
                            continue
                        run = model.NewBoolVar(f"run_a{agent_id}_s{s}_e{e}")
                        num_variables += 1
                        run_vars[(agent_id, s, e)] = run
                        runs_candidate_count_by_agent[agent_id] += 1
                        for i in range(s, e + 1):
                            model.Add(worked_ctx[(agent_id, i)] == 1).OnlyEnforceIf(run)
                            num_constraints += 1
                        if s > 0:
                            model.Add(worked_ctx[(agent_id, s - 1)] == 0).OnlyEnforceIf(run)
                            num_constraints += 1
                        if e < N_ctx - 1:
                            model.Add(worked_ctx[(agent_id, e + 1)] == 0).OnlyEnforceIf(run)
                            num_constraints += 1

                        model.Add(sum(minutes_ctx[(agent_id, i)] for i in range(s, e + 1)) <= 2880).OnlyEnforceIf(run)
                        num_constraints += 1

                        if L == 6:
                            if e + 2 >= N_ctx:
                                model.Add(run == 0)
                                num_constraints += 1
                            else:
                                model.Add(off_ctx[(agent_id, e + 1)] == 1).OnlyEnforceIf(run)
                                num_constraints += 1
                                model.Add(off_ctx[(agent_id, e + 2)] == 1).OnlyEnforceIf(run)
                                num_constraints += 1

                for i in range(N_ctx):
                    covering_runs = [
                        run
                        for (a, s, e), run in run_vars.items()
                        if a == agent_id and s <= i <= e
                    ]
                    model.Add(sum(covering_runs) == worked_ctx[(agent_id, i)])
                    num_constraints += 1

            run_feasible_candidate_count_by_agent: dict[int, int] = {agent_id: 0 for agent_id in ordered_agent_ids}
            can_work_ctx: dict[tuple[int, int], bool] = {}
            can_off_ctx: dict[tuple[int, int], bool] = {}
            for agent_id in ordered_agent_ids:
                for ci, day_date in enumerate(context_days):
                    key = (agent_id, day_date)
                    if ci in in_window_ctx_indices:
                        di = date_to_period_index[day_date]
                        day_combo_ids = [c for (a, d, c) in y if a == agent_id and d == di]
                        can_work_ctx[(agent_id, ci)] = any(self._is_work_combo(combo_by_id[cid]) for cid in day_combo_ids)
                        if daily_choice_mode == "at_most_one":
                            can_off_ctx[(agent_id, ci)] = True
                        else:
                            can_off_ctx[(agent_id, ci)] = any(combo_by_id[cid].day_kind == DayKind.REST for cid in day_combo_ids)
                    else:
                        day_type_ctx = solver_input.existing_day_type_by_agent_day_ctx.get(key, DayType.REST.value)
                        can_work_ctx[(agent_id, ci)] = day_type_ctx in self.GPT_DAY_TYPES
                        can_off_ctx[(agent_id, ci)] = day_type_ctx in self.RPDOUBLE_OFF_DAY_TYPES

            for agent_id in ordered_agent_ids:
                for s in range(N_ctx):
                    for e in range(s, min(N_ctx, s + 6)):
                        L = e - s + 1
                        if L < 3:
                            continue
                        if not all(can_work_ctx[(agent_id, i)] for i in range(s, e + 1)):
                            continue
                        if s > 0 and not can_off_ctx[(agent_id, s - 1)]:
                            continue
                        if e < N_ctx - 1 and not can_off_ctx[(agent_id, e + 1)]:
                            continue
                        if L == 6:
                            if e + 2 >= N_ctx:
                                continue
                            if not (can_off_ctx[(agent_id, e + 1)] and can_off_ctx[(agent_id, e + 2)]):
                                continue
                        run_feasible_candidate_count_by_agent[agent_id] += 1

            stats["run_feasible_candidate_count_by_agent"] = run_feasible_candidate_count_by_agent
            stats["worked_ctx_window_fixed_days_count_by_agent"] = worked_ctx_window_fixed_days_count_by_agent
        is_work_by_agent_day: dict[tuple[int, int], cp_model.IntVar] = {}
        stability_change_vars_by_agent: dict[int, list[cp_model.IntVar]] = {agent_id: [] for agent_id in ordered_agent_ids}
        work_block_start_vars_by_agent: dict[int, list[cp_model.IntVar]] = {agent_id: [] for agent_id in ordered_agent_ids}
        rpdouble_soft_vars_by_agent: dict[int, list[cp_model.IntVar]] = {agent_id: [] for agent_id in ordered_agent_ids}

        for agent_id in ordered_agent_ids:
            for di in range(len(dates)):
                work_vars = [
                    var
                    for (a, d, c), var in y.items()
                    if a == agent_id and d == di and self._is_work_combo(combo_by_id[c])
                ]
                is_work = model.NewBoolVar(f"is_work_a{agent_id}_d{di}")
                num_variables += 1
                if work_vars:
                    model.Add(is_work == sum(work_vars))
                else:
                    model.Add(is_work == 0)
                num_constraints += 1
                is_work_by_agent_day[(agent_id, di)] = is_work

                start_work = model.NewBoolVar(f"start_work_a{agent_id}_d{di}")
                num_variables += 1
                if di == 0:
                    model.Add(start_work == is_work)
                    num_constraints += 1
                else:
                    prev_is_work = is_work_by_agent_day[(agent_id, di - 1)]
                    model.Add(start_work <= is_work)
                    model.Add(start_work <= 1 - prev_is_work)
                    model.Add(start_work >= is_work - prev_is_work)
                    num_constraints += 3
                work_block_start_vars_by_agent[agent_id].append(start_work)

        for agent_id in ordered_agent_ids:
            for di in range(1, len(dates)):
                prev_is_work = is_work_by_agent_day[(agent_id, di - 1)]
                curr_is_work = is_work_by_agent_day[(agent_id, di)]

                both_work = model.NewBoolVar(f"both_work_a{agent_id}_d{di}")
                num_variables += 1
                model.Add(both_work <= prev_is_work)
                model.Add(both_work <= curr_is_work)
                model.Add(both_work >= prev_is_work + curr_is_work - 1)
                num_constraints += 3

                same_work_combo = model.NewBoolVar(f"same_work_combo_a{agent_id}_d{di}")
                num_variables += 1
                same_combo_vars = []
                for combo in sorted_work_combos:
                    prev_var = y.get((agent_id, di - 1, combo.id))
                    curr_var = y.get((agent_id, di, combo.id))
                    if prev_var is None or curr_var is None:
                        continue
                    same_c = model.NewBoolVar(f"same_c_a{agent_id}_d{di}_c{combo.id}")
                    num_variables += 1
                    model.Add(same_c <= prev_var)
                    model.Add(same_c <= curr_var)
                    model.Add(same_c >= prev_var + curr_var - 1)
                    num_constraints += 3
                    same_combo_vars.append(same_c)

                if same_combo_vars:
                    model.Add(same_work_combo == sum(same_combo_vars))
                else:
                    model.Add(same_work_combo == 0)
                model.Add(same_work_combo <= both_work)
                num_constraints += 2

                change_work = model.NewBoolVar(f"change_work_a{agent_id}_d{di}")
                num_variables += 1
                model.Add(change_work + same_work_combo == both_work)
                num_constraints += 1
                stability_change_vars_by_agent[agent_id].append(change_work)

                rpdouble_soft = model.NewBoolVar(f"rpdouble_soft_a{agent_id}_d{di - 1}")
                num_variables += 1
                model.Add(rpdouble_soft <= 1 - prev_is_work)
                model.Add(rpdouble_soft <= 1 - curr_is_work)
                model.Add(rpdouble_soft >= (1 - prev_is_work) + (1 - curr_is_work) - 1)
                num_constraints += 3
                rpdouble_soft_vars_by_agent[agent_id].append(rpdouble_soft)

        diversity_vars_by_agent: dict[int, cp_model.IntVar] = {}
        used_tranche_vars_by_agent: dict[int, dict[int, cp_model.IntVar]] = {agent_id: {} for agent_id in ordered_agent_ids}
        M_days = len(dates)
        for agent_id in ordered_agent_ids:
            eligible_tranche_ids = sorted(
                {
                    combo_main_tranche_id[combo_id]
                    for combo_id in combo_by_id
                    if combo_main_tranche_id[combo_id] is not None and any((agent_id, di, combo_id) in y for di in range(len(dates)))
                }
            )
            for tranche_id in eligible_tranche_ids:
                tranche_count = model.NewIntVar(0, M_days, f"tranche_count_a{agent_id}_t{tranche_id}")
                used_tranche = model.NewBoolVar(f"used_tranche_a{agent_id}_t{tranche_id}")
                num_variables += 2
                terms = [
                    y[(agent_id, di, combo_id)]
                    for di in range(len(dates))
                    for combo_id in combo_by_id
                    if (agent_id, di, combo_id) in y and combo_main_tranche_id[combo_id] == tranche_id
                ]
                if terms:
                    model.Add(tranche_count == sum(terms))
                else:
                    model.Add(tranche_count == 0)
                model.Add(tranche_count <= M_days * used_tranche)
                model.Add(tranche_count >= used_tranche)
                num_constraints += 3
                used_tranche_vars_by_agent[agent_id][tranche_id] = used_tranche

            diversity = model.NewIntVar(0, len(used_tranche_vars_by_agent[agent_id]), f"diversity_a{agent_id}")
            num_variables += 1
            if used_tranche_vars_by_agent[agent_id]:
                model.Add(diversity == sum(used_tranche_vars_by_agent[agent_id].values()))
            else:
                model.Add(diversity == 0)
            num_constraints += 1
            diversity_vars_by_agent[agent_id] = diversity

        work_days_by_agent: dict[int, cp_model.IntVar] = {}
        work_minutes_by_agent: dict[int, cp_model.IntVar] = {}
        night_days_by_agent: dict[int, cp_model.IntVar] = {}
        amplitude_by_agent: dict[int, cp_model.IntVar] = {}
        useless_work_vars: list[cp_model.IntVar] = []
        for agent_id in ordered_agent_ids:
            work_day_vars: list[cp_model.IntVar] = []
            work_minutes_day_exprs = []
            night_day_vars: list[cp_model.IntVar] = []
            amplitude_day_exprs = []
            for di in range(len(dates)):
                non_empty_vars = [
                    var
                    for (a, d, c), var in y.items()
                    if a == agent_id and d == di and combo_by_id[c].tranche_ids
                ]
                work_day = model.NewIntVar(0, 1, f"work_day_a{agent_id}_d{di}")
                num_variables += 1
                if non_empty_vars:
                    model.Add(work_day == sum(non_empty_vars))
                else:
                    model.Add(work_day == 0)
                num_constraints += 1
                work_day_vars.append(work_day)
                if di not in demanded_day_idx_set:
                    useless_work_vars.append(work_day)

                combo_work_expr = sum(
                    y[(agent_id, di, combo_id)] * combo_by_id[combo_id].work_minutes
                    for combo_id in combo_by_id
                    if (agent_id, di, combo_id) in y
                )
                work_minutes_day_exprs.append(combo_work_expr)

                night_day = model.NewIntVar(0, 1, f"night_day_a{agent_id}_d{di}")
                num_variables += 1
                night_vars = [
                    var
                    for (a, d, c), var in y.items()
                    if a == agent_id and d == di and combo_by_id[c].involves_night
                ]
                if night_vars:
                    model.Add(night_day == sum(night_vars))
                else:
                    model.Add(night_day == 0)
                num_constraints += 1
                night_day_vars.append(night_day)

                amplitude_day_exprs.append(
                    sum(
                        y[(agent_id, di, combo_id)] * combo_by_id[combo_id].amplitude_minutes
                        for combo_id in combo_by_id
                        if (agent_id, di, combo_id) in y
                    )
                )

            work_days = model.NewIntVar(0, len(dates), f"work_days_a{agent_id}")
            num_variables += 1
            model.Add(work_days == sum(work_day_vars))
            num_constraints += 1
            work_days_by_agent[agent_id] = work_days

            max_minutes_per_day = max((combo.work_minutes for combo in combo_by_id.values()), default=0)
            max_minutes = len(dates) * max_minutes_per_day
            work_minutes = model.NewIntVar(0, max_minutes, f"work_minutes_a{agent_id}")
            num_variables += 1
            model.Add(work_minutes == sum(work_minutes_day_exprs))
            num_constraints += 1
            work_minutes_by_agent[agent_id] = work_minutes

            night_days = model.NewIntVar(0, len(dates), f"night_days_a{agent_id}")
            num_variables += 1
            model.Add(night_days == sum(night_day_vars))
            num_constraints += 1
            night_days_by_agent[agent_id] = night_days

            max_amplitude_per_day = max((combo.amplitude_minutes for combo in combo_by_id.values()), default=0)
            max_amplitude = len(dates) * max_amplitude_per_day
            amplitude_sum = model.NewIntVar(0, max_amplitude, f"amplitude_sum_a{agent_id}")
            num_variables += 1
            model.Add(amplitude_sum == sum(amplitude_day_exprs))
            num_constraints += 1
            amplitude_by_agent[agent_id] = amplitude_sum

        max_work_days = model.NewIntVar(0, len(dates), "max_work_days")
        min_work_days = model.NewIntVar(0, len(dates), "min_work_days")
        num_variables += 2
        if work_days_by_agent:
            model.AddMaxEquality(max_work_days, list(work_days_by_agent.values()))
            model.AddMinEquality(min_work_days, list(work_days_by_agent.values()))
            num_constraints += 2
        else:
            model.Add(max_work_days == 0)
            model.Add(min_work_days == 0)
            num_constraints += 2

        max_work_minutes = model.NewIntVar(0, 60_000, "max_work_minutes")
        min_work_minutes = model.NewIntVar(0, 60_000, "min_work_minutes")
        max_nights = model.NewIntVar(0, len(dates), "max_nights")
        min_nights = model.NewIntVar(0, len(dates), "min_nights")
        total_night_days = model.NewIntVar(0, len(dates) * max(1, len(ordered_agent_ids)), "total_night_days")
        total_amplitude_cost = model.NewIntVar(0, 60_000, "total_amplitude_cost")
        useless_work_total = model.NewIntVar(0, len(useless_work_vars), "useless_work_total")
        num_variables += 7
        if work_minutes_by_agent:
            model.AddMaxEquality(max_work_minutes, list(work_minutes_by_agent.values()))
            model.AddMinEquality(min_work_minutes, list(work_minutes_by_agent.values()))
            num_constraints += 2
        else:
            model.Add(max_work_minutes == 0)
            model.Add(min_work_minutes == 0)
            num_constraints += 2

        if night_days_by_agent:
            model.AddMaxEquality(max_nights, list(night_days_by_agent.values()))
            model.AddMinEquality(min_nights, list(night_days_by_agent.values()))
            model.Add(total_night_days == sum(night_days_by_agent.values()))
            num_constraints += 3
        else:
            model.Add(max_nights == 0)
            model.Add(min_nights == 0)
            model.Add(total_night_days == 0)
            num_constraints += 3

        default_enable_symmetry_breaking = profile in {"balanced", "high"}
        enable_symmetry_breaking = default_enable_symmetry_breaking if solver_input.enable_symmetry_breaking is None else bool(solver_input.enable_symmetry_breaking)
        symmetry_constraints_count = 0
        if enable_symmetry_breaking:
            for i in range(len(ordered_agent_ids) - 1):
                a1 = ordered_agent_ids[i]
                a2 = ordered_agent_ids[i + 1]
                if a1 in work_days_by_agent and a2 in work_days_by_agent:
                    model.Add(work_days_by_agent[a1] >= work_days_by_agent[a2])
                    symmetry_constraints_count += 1
                if a1 in night_days_by_agent and a2 in night_days_by_agent:
                    model.Add(night_days_by_agent[a1] >= night_days_by_agent[a2])
                    symmetry_constraints_count += 1
            num_constraints += symmetry_constraints_count
        stats["symmetry_breaking_enabled"] = bool(enable_symmetry_breaking)
        stats["symmetry_constraints_count"] = int(symmetry_constraints_count)

        if amplitude_by_agent:
            model.Add(total_amplitude_cost == sum(amplitude_by_agent.values()))
        else:
            model.Add(total_amplitude_cost == 0)
        num_constraints += 1

        understaff_weighted_sum = model.NewIntVar(0, max(0, total_required_count * self.W_UNDERSTAFF_WEEKDAY_DAY), "understaff_weighted_sum")
        num_variables += 1
        if weighted_understaff_terms:
            model.Add(understaff_weighted_sum == sum(weighted_understaff_terms))
        else:
            model.Add(understaff_weighted_sum == 0)
        num_constraints += 1

        if useless_work_vars:
            model.Add(useless_work_total == sum(useless_work_vars))
        else:
            model.Add(useless_work_total == 0)
        num_constraints += 1

        stability_changes_total = model.NewIntVar(0, len(ordered_agent_ids) * max(0, len(dates) - 1), "stability_changes_total")
        work_blocks_starts_total = model.NewIntVar(0, len(ordered_agent_ids) * len(dates), "work_blocks_starts_total")
        rpdouble_soft_total = model.NewIntVar(0, len(ordered_agent_ids) * max(0, len(dates) - 1), "rpdouble_soft_total")
        tranche_diversity_total = model.NewIntVar(0, len(ordered_agent_ids) * len(solver_input.tranches), "tranche_diversity_total")
        understaff_smooth_weighted_sum = model.NewIntVar(0, max(0, sum(self._understaff_priority_weight_for_demand(day_date=d.day_date, tranche=tranche_by_id.get(d.tranche_id)) * (max(0, d.required_count) ** 2) for d in solver_input.coverage_demands)), "understaff_smooth_weighted_sum")
        num_variables += 5

        all_changes = [var for vars_list in stability_change_vars_by_agent.values() for var in vars_list]
        all_starts = [var for vars_list in work_block_start_vars_by_agent.values() for var in vars_list]
        all_rpdouble = [var for vars_list in rpdouble_soft_vars_by_agent.values() for var in vars_list]
        if all_changes:
            model.Add(stability_changes_total == sum(all_changes))
        else:
            model.Add(stability_changes_total == 0)
        if all_starts:
            model.Add(work_blocks_starts_total == sum(all_starts))
        else:
            model.Add(work_blocks_starts_total == 0)
        if all_rpdouble:
            model.Add(rpdouble_soft_total == sum(all_rpdouble))
        else:
            model.Add(rpdouble_soft_total == 0)
        if diversity_vars_by_agent:
            model.Add(tranche_diversity_total == sum(diversity_vars_by_agent.values()))
        else:
            model.Add(tranche_diversity_total == 0)
        if weighted_understaff_smooth_terms:
            model.Add(understaff_smooth_weighted_sum == sum(weighted_understaff_smooth_terms))
        else:
            model.Add(understaff_smooth_weighted_sum == 0)
        num_constraints += 5

        understaff_total_unweighted = model.NewIntVar(0, total_required_count, "understaff_total_unweighted")
        num_variables += 1
        if understaff_vars:
            model.Add(understaff_total_unweighted == sum(understaff_vars))
        else:
            model.Add(understaff_total_unweighted == 0)
        num_constraints += 1

        objective = (
            self.W_COVER * understaff_weighted_sum
            + self.W_NIGHTS_TOTAL * total_night_days
            + self.W_NIGHTS_SPREAD * (max_nights - min_nights)
            + self.W_FAIR_MINUTES_SPREAD * (max_work_minutes - min_work_minutes)
            + self.W_FAIR_DAYS_SPREAD * (max_work_days - min_work_days)
            + self.W_AMPLITUDE * total_amplitude_cost
            + self.W_USELESS_WORK * useless_work_total
            + self.W_STABILITY_CHANGE * stability_changes_total
            + self.W_WORK_BLOCKS * work_blocks_starts_total
            - self.W_RPDOUBLE_BONUS * rpdouble_soft_total
            - self.W_TRANCHE_DIVERSITY * tranche_diversity_total
            + self.W_UNDERSTAFF_SMOOTH * understaff_smooth_weighted_sum
        )

        def _normalize_status(raw_status: int, wall_time: float, budget_seconds: float) -> tuple[str, str, bool]:
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

        def _new_solver(budget_seconds: float) -> cp_model.CpSolver:
            solver = cp_model.CpSolver()
            if budget_seconds > 0:
                solver.parameters.max_time_in_seconds = budget_seconds
                applied = float(time_limit_seconds if time_limit_seconds > 0 else budget_seconds)
                stats["solver_max_time_seconds_applied"] = max(float(stats.get("solver_max_time_seconds_applied", 0.0)), applied)
            solver.parameters.num_search_workers = 1
            solver.parameters.random_seed = int(solver_input.seed or 0)
            return solver

        def _effective_cp_sat_params(solver: cp_model.CpSolver, budget_seconds: float) -> dict[str, object]:
            params: dict[str, object] = {
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

        class _TraceCallback(cp_model.CpSolverSolutionCallback):
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

        y_keys = sorted(y.keys())
        y_proto_idx = {key: y[key].Index() for key in y_keys}

        default_enable_decision_strategy = profile in {"balanced", "high"}
        enable_decision_strategy = default_enable_decision_strategy if solver_input.enable_decision_strategy is None else bool(solver_input.enable_decision_strategy)
        # Phase 1 is always guided by decision strategy in V3.2.
        enable_decision_strategy_phase1 = True
        day_scores: list[tuple[int, object]] = []
        required_by_day: dict[int, int] = {}
        for demand in solver_input.coverage_demands:
            di = date_to_index[demand.day_date]
            required_by_day[di] = required_by_day.get(di, 0) + max(0, demand.required_count)
        day_scores = sorted(required_by_day.items(), key=lambda item: (-item[1], dates[item[0]]))
        prioritized_y: list[cp_model.IntVar] = []
        seen_ids: set[int] = set()
        for di, _score in day_scores:
            demand_triplets = []
            for demand in solver_input.coverage_demands:
                ddi = date_to_index[demand.day_date]
                if ddi != di:
                    continue
                demand_triplets.append((int(demand.poste_id or tranche_by_id[demand.tranche_id].poste_id), int(demand.tranche_id), vars_by_demand.get((ddi, demand.tranche_id), [])))
            demand_triplets.sort(key=lambda x: (x[0], x[1]))
            for poste_id, tranche_id, dvars in demand_triplets:
                keys_for_vars = []
                for v in dvars:
                    key = next((k for k,val in y.items() if val is v), None)
                    if key is None:
                        continue
                    aid, _di, cid = key
                    keys_for_vars.append((aid, cid, v))
                keys_for_vars.sort(key=lambda t: (t[0], t[1]))
                for _aid,_cid,v in keys_for_vars:
                    vid=id(v)
                    if vid in seen_ids:
                        continue
                    seen_ids.add(vid)
                    prioritized_y.append(v)
                    if len(prioritized_y) >= 5000:
                        break
                if len(prioritized_y) >= 5000:
                    break
            if len(prioritized_y) >= 5000:
                break
        if enable_decision_strategy_phase1 and prioritized_y:
            model.AddDecisionStrategy(prioritized_y, cp_model.CHOOSE_FIRST, cp_model.SELECT_MAX_VALUE)
            stats["decision_strategy_enabled"] = True
        elif enable_decision_strategy:
            stats["decision_strategy_enabled"] = True
        stats["decision_strategy_prioritized_vars_count"] = len(prioritized_y)
        stats["decision_strategy_day_scores_top"] = [
            {"day_date": dates[di].isoformat(), "score": int(score)}
            for di, score in day_scores[:5]
        ]

        def _solve_with_trace(solver: cp_model.CpSolver, mdl: cp_model.CpModel, cb: _TraceCallback | None = None) -> int:
            if cb is None:
                return solver.Solve(mdl)
            try:
                return solver.Solve(mdl, cb)
            except TypeError:
                return solver.Solve(mdl)

        def _extract_solution(solver: cp_model.CpSolver):
            assign = {(aid, di, cid): int(solver.Value(y[(aid, di, cid)])) for (aid, di, cid) in y_keys}
            run_assign = {(aid, si, ei): int(solver.Value(run_vars[(aid, si, ei)])) for (aid, si, ei) in sorted(run_vars.keys())} if run_vars else {}
            understaff_by_poste_unweighted: dict[int, int] = {}
            understaff_by_poste_weighted: dict[int, int] = {}
            understaff_by_poste_day: dict[tuple[int, int], int] = {}
            understaff_by_day_unweighted: dict[int, int] = {}
            understaff_by_day_weighted: dict[int, int] = {}
            for rec in demand_records:
                poste_id = int(rec["poste_id"])
                di = int(rec["day_index"])
                us = int(solver.Value(rec["understaff_var"]))
                if us <= 0:
                    continue
                understaff_by_poste_unweighted[poste_id] = understaff_by_poste_unweighted.get(poste_id, 0) + us
                weighted_us = int(rec["weight"]) * us
                understaff_by_poste_weighted[poste_id] = understaff_by_poste_weighted.get(poste_id, 0) + weighted_us
                key = (poste_id, di)
                understaff_by_poste_day[key] = understaff_by_poste_day.get(key, 0) + us
                understaff_by_day_unweighted[di] = understaff_by_day_unweighted.get(di, 0) + us
                understaff_by_day_weighted[di] = understaff_by_day_weighted.get(di, 0) + weighted_us
            return {
                "assignment_map": assign,
                "run_assignment_map": run_assign,
                "understaff_total_unweighted": int(solver.Value(understaff_total_unweighted)),
                "objective_value": int(solver.Value(objective)),
                "understaff_total_weighted": int(solver.Value(understaff_weighted_sum)),
                "understaff_by_poste_unweighted": understaff_by_poste_unweighted,
                "understaff_by_poste_weighted": understaff_by_poste_weighted,
                "understaff_by_poste_day": understaff_by_poste_day,
                "understaff_by_day_unweighted": understaff_by_day_unweighted,
                "understaff_by_day_weighted": understaff_by_day_weighted,
            }

        strategy = (solver_input.v3_strategy or "two_phase_lns").lower()
        default_phase1_fraction = {"fast": 0.2, "balanced": 0.1, "high": 0.15}.get(profile, 0.1)
        phase1_fraction = float(solver_input.phase1_fraction if solver_input.phase1_fraction is not None else default_phase1_fraction)
        phase1_seconds = float(solver_input.phase1_seconds) if solver_input.phase1_seconds is not None else max(2.0, min(10.0, time_limit_seconds * phase1_fraction))
        if time_limit_seconds > 0:
            phase1_seconds = min(phase1_seconds, time_limit_seconds)
        else:
            phase1_seconds = 0.0
        default_lns_iter = {"fast": 0.0, "balanced": 2.0, "high": 3.0}.get(profile, 2.0)
        lns_iter_seconds = float(solver_input.lns_iter_seconds if solver_input.lns_iter_seconds is not None else default_lns_iter)
        lns_min_remaining_seconds = float(solver_input.lns_min_remaining_seconds if solver_input.lns_min_remaining_seconds is not None else 1.0)
        lns_strict_improve = bool(solver_input.lns_strict_improve)
        lns_max_days_to_relax = int(solver_input.lns_max_days_to_relax) if solver_input.lns_max_days_to_relax is not None else 14
        lns_neighborhood_mode = str(getattr(solver_input, "lns_neighborhood_mode", "poste_only") or "poste_only").lower()
        allowed_neighborhood_modes = {"poste_only", "poste_plus_one", "top_days_global", "poste_plus_one_top_days", "mixed"}
        if lns_neighborhood_mode not in allowed_neighborhood_modes:
            lns_neighborhood_mode = "poste_only"
        min_lns_seconds = float(solver_input.min_lns_seconds if solver_input.min_lns_seconds is not None else (time_limit_seconds * 0.1 if time_limit_seconds > 0 else 0.0))
        phase2_max_fraction = float(solver_input.phase2_max_fraction_of_remaining if solver_input.phase2_max_fraction_of_remaining is not None else 0.7)
        phase2_no_improve_seconds = float(solver_input.phase2_no_improve_seconds) if solver_input.phase2_no_improve_seconds is not None else None
        lns_enabled = strategy in {"two_phase_lns", "lns_only"} and lns_iter_seconds > 0
        stats["lns_strict_improve"] = lns_strict_improve
        stats["lns_max_days_to_relax"] = lns_max_days_to_relax
        stats["lns_neighborhood_mode"] = lns_neighborhood_mode
        stats["lns_neighborhood_mode_requested"] = lns_neighborhood_mode
        stats["min_lns_seconds"] = min_lns_seconds

        started_at = time.monotonic()
        stats["model_build_wall_time_seconds"] = max(0.0, started_at - solve_started_at)
        best_solution = None
        trace_points: list[tuple[float, float, int]] = []
        time_to_first_feasible_seconds = None
        phase1_stats = {}
        phase2_stats = {}
        last_raw_status = None
        last_normalized_status = None
        last_wall_time = 0.0
        last_status_int = None

        if strategy != "lns_only":
            model.Minimize(understaff_total_unweighted)
            solver1 = _new_solver(phase1_seconds)
            stats.setdefault("cp_sat_params_effective", {})["phase1"] = _effective_cp_sat_params(solver1, phase1_seconds)
            cb1 = _TraceCallback(understaff_total_unweighted)
            status1 = _solve_with_trace(solver1, model, cb1)
            wall1 = float(solver1.WallTime())
            raw1, normalized1, timeout1 = _normalize_status(status1, wall1, phase1_seconds)
            last_wall_time = wall1
            last_status_int = int(status1)
            last_raw_status = raw1
            last_normalized_status = normalized1
            phase1_stats = {
                "phase1_time_limit_seconds": phase1_seconds,
                "phase1_wall_time_seconds": wall1,
                "phase1_solve_wall_time_seconds": wall1,
                "phase1_status_raw": raw1,
                "phase1_normalized_status": normalized1,
                "phase1_best_objective_value": float(getattr(solver1, "ObjectiveValue", lambda: 0.0)()) if status1 in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
            }
            if cb1.first_feasible_time is not None and time_to_first_feasible_seconds is None:
                time_to_first_feasible_seconds = cb1.first_feasible_time
            trace_points.extend(cb1.points)
            if status1 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                best_solution = _extract_solution(solver1)
                phase1_stats["phase1_understaff_total_unweighted"] = best_solution["understaff_total_unweighted"]
                phase1_stats["phase1_coverage_ratio_unweighted"] = max(0.0, 1.0 - (best_solution["understaff_total_unweighted"] / total_required_count)) if total_required_count else 1.0
            else:
                phase1_stats["phase1_understaff_total_unweighted"] = None
                phase1_stats["phase1_coverage_ratio_unweighted"] = None

            remaining_after_phase1 = max(0.0, time_limit_seconds - (time.monotonic() - started_at)) if time_limit_seconds > 0 else 0.0
            if strategy in {"two_phase", "two_phase_lns"} and remaining_after_phase1 > 0:
                min_lns_reserve = min(min_lns_seconds, remaining_after_phase1) if lns_enabled else 0.0
                phase2_budget_cap = max(0.0, remaining_after_phase1 - min_lns_reserve)
                phase2_budget_cap = min(phase2_budget_cap, remaining_after_phase1 * phase2_max_fraction)
                if phase2_budget_cap <= 0:
                    phase2_budget_cap = max(0.0, remaining_after_phase1 - min_lns_reserve)
                if best_solution is not None:
                    model.Add(understaff_total_unweighted <= int(best_solution["understaff_total_unweighted"]))
                model.Minimize(objective)
                if best_solution is not None:
                    for key in y_keys:
                        model.AddHint(y[key], int(best_solution["assignment_map"][key]))
                phase2_rebuild_started = time.monotonic()
                stats["phase2_model_rebuild_wall_time_seconds"] = 0.0
                stats["phase2_reused_model"] = True
                solver2 = _new_solver(phase2_budget_cap)
                stats.setdefault("cp_sat_params_effective", {})["phase2"] = _effective_cp_sat_params(solver2, phase2_budget_cap)
                cb2 = _TraceCallback(understaff_total_unweighted, stop_no_improve_after_seconds=phase2_no_improve_seconds)
                status2 = _solve_with_trace(solver2, model, cb2)
                wall2 = float(solver2.WallTime())
                stats["phase2_solve_wall_time_seconds"] = wall2
                raw2, normalized2, timeout2 = _normalize_status(status2, wall2, phase2_budget_cap)
                last_wall_time = wall2
                last_status_int = int(status2)
                last_raw_status = raw2
                last_normalized_status = normalized2
                phase2_stats = {
                    "phase2_time_limit_seconds": remaining_after_phase1,
                    "phase2_wall_time_seconds": wall2,
                    "phase2_solve_wall_time_seconds": wall2,
                    "phase2_status_raw": raw2,
                    "phase2_normalized_status": normalized2,
                    "phase2_best_objective_value": float(getattr(solver2, "ObjectiveValue", lambda: 0.0)()) if status2 in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None,
                    "phase2_non_regression_constraint_applied": best_solution is not None,
                    "phase2_non_regression_bound": int(best_solution["understaff_total_unweighted"]) if best_solution is not None else None,
                }
                if cb2.first_feasible_time is not None and time_to_first_feasible_seconds is None:
                    time_to_first_feasible_seconds = phase1_stats.get("phase1_wall_time_seconds", 0.0) + cb2.first_feasible_time
                trace_points.extend([(phase1_stats.get("phase1_wall_time_seconds", 0.0) + t, obj, us) for (t, obj, us) in cb2.points])
                if status2 in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                    cand = _extract_solution(solver2)
                    phase2_stats["phase2_understaff_total_unweighted"] = cand["understaff_total_unweighted"]
                    phase2_stats["phase2_coverage_ratio_unweighted"] = max(0.0, 1.0 - (cand["understaff_total_unweighted"] / total_required_count)) if total_required_count else 1.0
                    if best_solution is None or (cand["understaff_total_unweighted"], cand["objective_value"]) <= (best_solution["understaff_total_unweighted"], best_solution["objective_value"]):
                        best_solution = cand
                else:
                    phase2_stats["phase2_understaff_total_unweighted"] = None
                    phase2_stats["phase2_coverage_ratio_unweighted"] = None

        lns_started = time.monotonic()
        lns_result = LnsRunner(max_lns_history_items=self.MAX_LNS_HISTORY_ITEMS).run(
            best_solution=best_solution,
            stats=stats,
            solver_input=solver_input,
            demand_records=demand_records,
            dates=dates,
            started_at=started_at,
            time_limit_seconds=time_limit_seconds,
            lns_enabled=lns_enabled,
            lns_min_remaining_seconds=lns_min_remaining_seconds,
            lns_iter_seconds=lns_iter_seconds,
            lns_strict_improve=lns_strict_improve,
            lns_max_days_to_relax=lns_max_days_to_relax,
            lns_neighborhood_mode=lns_neighborhood_mode,
            min_remaining_seconds_to_run_iter=MIN_LNS_REMAINING_SECONDS_TO_RUN_ITER,
            lns_iter_overhead_seconds=LNS_ITER_OVERHEAD_SECONDS,
            min_lns_cp_sat_time_limit_seconds=MIN_LNS_CP_SAT_TIME_LIMIT_SECONDS,
            model=model,
            y_keys=y_keys,
            combo_by_id=combo_by_id,
            y_proto_idx=y_proto_idx,
            run_vars=run_vars,
            _new_solver=_new_solver,
            _effective_cp_sat_params=_effective_cp_sat_params,
            _normalize_status=_normalize_status,
            _extract_solution=_extract_solution,
        )
        best_solution = lns_result.best_solution
        lns_iterations = lns_result.lns_iterations
        lns_accept_count = lns_result.lns_accept_count
        lns_best_improvement_understaff = lns_result.lns_best_improvement_understaff
        lns_best_improvement_objective = lns_result.lns_best_improvement_objective
        lns_neighborhoods_tried = lns_result.lns_neighborhoods_tried

        if best_solution is None:
            stats["solve_wall_time_seconds"] = float(last_wall_time)
            stats["solve_time_seconds"] = float(last_wall_time)
            stats["solver_status_int"] = last_status_int
            stats["solver_status"] = last_raw_status or "UNKNOWN"
            stats["solver_status_raw"] = last_raw_status or "UNKNOWN"
            stats["normalized_solver_status"] = last_normalized_status or "UNKNOWN"
            stats["is_timeout"] = (last_normalized_status == "TIMEOUT")
            stats["time_limit_reached"] = stats["is_timeout"]
            if last_normalized_status == "TIMEOUT":
                raise TimeoutError("timeout", stats=stats_collector.finalize(stats))
            stats["timeout_confidence"] = "low"
            raise InfeasibleError("infeasible", stats=stats_collector.finalize(stats))

        # Evaluate final incumbent for reporting and extraction.
        eval_model = model.Clone()
        for key in y_keys:
            eval_model.Add(y[key] == int(best_solution["assignment_map"][key]))
        eval_solver = _new_solver(1.0)
        eval_status = eval_solver.Solve(eval_model)
        if eval_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise InfeasibleError("infeasible", stats=stats_collector.finalize(stats))

        status = eval_status
        wall_time = float(time.monotonic() - started_at)
        time_limit_reached = bool((last_normalized_status == "TIMEOUT") or (time_limit_seconds > 0 and wall_time >= time_limit_seconds * 0.95))
        normalized_solver_status = "TIMEOUT" if time_limit_reached else "FEASIBLE"

        stats["time_limit_seconds"] = time_limit_seconds
        stats["solve_wall_time_seconds"] = wall_time
        stats["solve_time_seconds"] = wall_time
        stats["solver_status_int"] = int(status)
        stats["num_variables"] = num_variables
        stats["num_constraints"] = num_constraints
        stats["coverage_constraints_count"] = coverage_constraints_count
        stats["num_rest_constraints"] = rest_constraints_count
        stats["solver_status"] = "FEASIBLE"
        stats["solver_status_raw"] = "FEASIBLE"
        stats["normalized_solver_status"] = normalized_solver_status
        stats["is_timeout"] = bool(time_limit_reached)
        stats["time_limit_reached"] = bool(time_limit_reached)
        stats["solver_max_time_seconds_applied"] = time_limit_seconds
        stats.update(phase1_stats)
        stats.update(phase2_stats)
        stats["lns_enabled"] = bool(lns_enabled)
        stats["lns_iterations"] = lns_iterations
        stats["lns_total_wall_time_seconds"] = float(time.monotonic() - lns_started) if lns_enabled else 0.0
        stats["lns_iter_time_seconds"] = lns_iter_seconds
        stats["lns_best_improvement_understaff_unweighted"] = lns_best_improvement_understaff
        stats["lns_best_improvement_objective"] = lns_best_improvement_objective
        stats["lns_best_understaff_total_unweighted"] = int(best_solution["understaff_total_unweighted"]) if best_solution is not None else None
        stats["lns_best_objective_value"] = int(best_solution["objective_value"]) if best_solution is not None else None
        stats["lns_accept_count"] = lns_accept_count
        stats["lns_accept_count_total"] = lns_accept_count
        stats["lns_neighborhoods_tried_by_poste"] = lns_neighborhoods_tried
        stats["time_to_first_feasible_seconds"] = time_to_first_feasible_seconds
        stats["best_objective_over_time_points"] = [{"t": round(t, 3), "obj": obj, "understaff_unweighted": us} for (t, obj, us) in trace_points[:200]]
        assignments: list[SolverAssignment] = []
        assigned_day_by_agent: set[tuple[int, int]] = set()
        for (agent_id, di, combo_id), var in y.items():
            if eval_solver.Value(var) != 1:
                continue
            combo = combo_by_id[combo_id]
            if combo.tranche_ids:
                assigned_day_by_agent.add((agent_id, di))
                for tranche_id in combo.tranche_ids:
                    assignments.append(SolverAssignment(agent_id=agent_id, day_date=dates[di], tranche_id=tranche_id))

        assignments.sort(key=lambda item: (item.day_date, item.agent_id, item.tranche_id))

        agent_days: list[SolverAgentDay] = []
        for day_date in dates:
            di = date_to_index[day_date]
            for agent_id in ordered_agent_ids:
                if (agent_id, di) in assigned_day_by_agent:
                    day_type = DayType.WORKING.value
                else:
                    day_type = solver_input.existing_day_type_by_agent_day.get((agent_id, day_date), DayType.REST.value)
                agent_days.append(
                    SolverAgentDay(
                        agent_id=agent_id,
                        day_date=day_date,
                        day_type=day_type,
                        description=None,
                        is_off_shift=False,
                    )
                )

        objective_value = int(best_solution["objective_value"])
        understaff_total = int(best_solution["understaff_total_unweighted"])
        understaff_total_weighted = int(best_solution["understaff_total_weighted"])
        coverage_ratio = 1.0
        if total_required_count > 0:
            coverage_ratio = max(0.0, 1.0 - (understaff_total / total_required_count))
        coverage_ratio_weighted = 1.0
        if total_required_weighted > 0:
            coverage_ratio_weighted = max(0.0, 1.0 - (understaff_total_weighted / total_required_weighted))
        work_values = [eval_solver.Value(work_days_by_agent[agent_id]) for agent_id in ordered_agent_ids]
        workload_min = min(work_values) if work_values else 0
        workload_max = max(work_values) if work_values else 0
        workload_avg = (sum(work_values) / len(work_values)) if work_values else 0.0
        stability_changes_by_agent = {
            agent_id: sum(eval_solver.Value(var) for var in stability_change_vars_by_agent.get(agent_id, []))
            for agent_id in ordered_agent_ids
        }
        work_blocks_starts_by_agent = {
            agent_id: sum(eval_solver.Value(var) for var in work_block_start_vars_by_agent.get(agent_id, []))
            for agent_id in ordered_agent_ids
        }
        rpdouble_soft_by_agent = {
            agent_id: sum(eval_solver.Value(var) for var in rpdouble_soft_vars_by_agent.get(agent_id, []))
            for agent_id in ordered_agent_ids
        }
        tranche_diversity_by_agent = {
            agent_id: eval_solver.Value(diversity_vars_by_agent.get(agent_id, 0)) if agent_id in diversity_vars_by_agent else 0
            for agent_id in ordered_agent_ids
        }

        combo_ids_used: set[int] = set()
        for (_agent_id, _di, combo_id), var in y.items():
            if eval_solver.Value(var) == 1:
                combo_ids_used.add(combo_id)

        runs_selected_by_agent = {
            agent_id: sum(
                eval_solver.Value(run)
                for (a, _s, _e), run in run_vars.items()
                if a == agent_id
            )
            for agent_id in ordered_agent_ids
        } if apply_gpt_rules else {}
        max_possible_runs_by_agent = {
            agent_id: len(context_days) // 3
            for agent_id in ordered_agent_ids
        } if apply_gpt_rules else {}


        understaff_day_weighted: dict[str, int] = {}
        understaff_day_unweighted: dict[str, int] = {}
        top_understaff_days = []
        for rec in demand_records:
            day_key = rec["day_date"].isoformat()
            us = int(eval_solver.Value(rec["understaff_var"]))
            wt = int(rec["weight"]) * us
            understaff_day_unweighted[day_key] = understaff_day_unweighted.get(day_key, 0) + us
            understaff_day_weighted[day_key] = understaff_day_weighted.get(day_key, 0) + wt
        for day_key in sorted(understaff_day_unweighted, key=lambda d: (-understaff_day_unweighted[d], -understaff_day_weighted.get(d, 0), d))[:10]:
            top_understaff_days.append({"day_date": day_key, "understaff_unweighted": understaff_day_unweighted[day_key], "understaff_weighted": understaff_day_weighted.get(day_key, 0)})
        stats["understaff_by_day_weighted"] = understaff_day_weighted
        stats["smoothing_term_components_count"] = len(weighted_understaff_smooth_terms)
        stats["top_understaff_days"] = top_understaff_days
        stats.update(
            {
                "solver_status": "FEASIBLE",
                "solver_status_raw": "FEASIBLE",
                "normalized_solver_status": normalized_solver_status,
                "is_timeout": bool(time_limit_reached),
                "time_limit_reached": bool(time_limit_reached),
                "score": objective_value,
                "objective_value": objective_value,
                "coverage_ratio": coverage_ratio,
                "understaff_total": understaff_total,
                "understaff_total_weighted": understaff_total_weighted,
                "coverage_ratio_weighted": coverage_ratio_weighted,
                "useless_work_total": eval_solver.Value(useless_work_total),
                "num_combos_used_in_solution": len(combo_ids_used),
                "workload_min": workload_min,
                "workload_max": workload_max,
                "workload_avg": workload_avg,
                "max_work_days": eval_solver.Value(max_work_days),
                "min_work_days": eval_solver.Value(min_work_days),
                "nights_total": eval_solver.Value(total_night_days),
                "nights_min": eval_solver.Value(min_nights),
                "nights_max": eval_solver.Value(max_nights),
                "amplitude_cost_total": eval_solver.Value(total_amplitude_cost),
                "stability_changes_total": eval_solver.Value(stability_changes_total),
                "stability_changes_by_agent": stability_changes_by_agent,
                "work_blocks_starts_total": eval_solver.Value(work_blocks_starts_total),
                "work_blocks_starts_by_agent": work_blocks_starts_by_agent,
                "rpdouble_soft_total": eval_solver.Value(rpdouble_soft_total),
                "rpdouble_soft_by_agent": rpdouble_soft_by_agent,
                "runs_selected_total": sum(runs_selected_by_agent.values()) if apply_gpt_rules else 0,
                "runs_selected_by_agent": runs_selected_by_agent,
                "runs_candidate_count_by_agent": runs_candidate_count_by_agent if apply_gpt_rules else {},
                "max_possible_runs_by_agent": max_possible_runs_by_agent,
                "tranche_diversity_total": eval_solver.Value(tranche_diversity_total),
                "tranche_diversity_by_agent": tranche_diversity_by_agent,
                "understaff_smooth_weighted_sum": eval_solver.Value(understaff_smooth_weighted_sum),
                "objective_terms": {
                    "understaff_weighted": understaff_total_weighted,
                    "understaff_smooth_weighted": eval_solver.Value(understaff_smooth_weighted_sum),
                    "nights_total": eval_solver.Value(total_night_days),
                    "nights_spread": eval_solver.Value(max_nights) - eval_solver.Value(min_nights),
                    "fair_minutes_spread": eval_solver.Value(max_work_minutes) - eval_solver.Value(min_work_minutes),
                    "fair_days_spread": eval_solver.Value(max_work_days) - eval_solver.Value(min_work_days),
                    "amplitude_cost": eval_solver.Value(total_amplitude_cost),
                    "useless_work": eval_solver.Value(useless_work_total),
                    "stability_changes": eval_solver.Value(stability_changes_total),
                    "work_blocks_starts": eval_solver.Value(work_blocks_starts_total),
                    "rpdouble_soft_bonus": eval_solver.Value(rpdouble_soft_total),
                    "tranche_diversity_bonus": eval_solver.Value(tranche_diversity_total),
                },
                "num_assignments": len(assignments),
            }
        )

        stats = stats_collector.finalize(stats)

        return SolverOutput(
            agent_days=agent_days,
            assignments=assignments,
            stats=stats,
        )
