from __future__ import annotations

from datetime import timedelta

from ortools.sat.python import cp_model

from core.domain.enums.day_type import DayType

from .models import InfeasibleError, SolverAgentDay, SolverAssignment, SolverInput, SolverOutput, TimeoutError
from .rh_combos import DayCombo, DefaultRhComboRulesEngine, build_day_combos_for_poste, build_rest_compatibility


class OrtoolsSolver:
    WEEKDAY_UNDERSTAFF_WEIGHT = 10
    WEEKEND_UNDERSTAFF_WEIGHT = 1

    W_COVER = 1_000_000
    W_NIGHTS_TOTAL = 10_000
    W_NIGHTS_SPREAD = 5_000
    W_FAIR_MINUTES_SPREAD = 1_000
    W_FAIR_DAYS_SPREAD = 500
    W_AMPLITUDE = 10
    W_USELESS_WORK = 50

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

    @classmethod
    def _understaff_weight_for_day(cls, day_date) -> int:
        return cls.WEEKDAY_UNDERSTAFF_WEIGHT if day_date.weekday() < 5 else cls.WEEKEND_UNDERSTAFF_WEIGHT

    def generate(self, solver_input: SolverInput) -> SolverOutput:
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
                    )
                )
                next_combo_id += 1

        combo_by_id = {combo.id: combo for combo in combos}
        sorted_combos = sorted(combos, key=lambda combo: ((combo.poste_id if combo.poste_id is not None else -1), combo.id))
        sorted_work_combos = [combo for combo in sorted_combos if combo.poste_id is not None]
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
            self._understaff_weight_for_day(demand.day_date) * max(0, demand.required_count)
            for demand in solver_input.coverage_demands
        )
        stats = {
            "solver_status": None,
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
            "objective_terms": {
                "understaff_weighted": 0,
                "nights_total": 0,
                "nights_spread": 0,
                "fair_minutes_spread": 0,
                "fair_days_spread": 0,
                "amplitude_cost": 0,
                "useless_work": 0,
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
        if missing_tranche_ids:
            stats["solver_status"] = "INFEASIBLE"
            stats["solver_status_raw"] = "PRECHECK_INFEASIBLE"
            stats["normalized_solver_status"] = "INFEASIBLE"
            stats["is_timeout"] = False
            raise InfeasibleError("infeasible", stats=stats)

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

        coverage_constraints_count = 0
        understaff_vars: list[cp_model.IntVar] = []
        weighted_understaff_terms: list[cp_model.LinearExprT] = []
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
            weighted_understaff_terms.append(self._understaff_weight_for_day(demand.day_date) * understaff)
            coverage_constraints_count += 1

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

        if apply_gpt_rules:
            worked_day_var: dict[tuple[int, int], cp_model.IntVar] = {}
            work_minutes_var: dict[tuple[int, int], cp_model.IntVar] = {}
            is_real_work_var: dict[tuple[int, int], cp_model.IntVar] = {}
            is_off_for_rpdouble_var: dict[tuple[int, int], cp_model.IntVar] = {}
            worked_day_const: dict[tuple[int, int], int] = {}
            work_minutes_const: dict[tuple[int, int], int] = {}
            is_real_work_const: dict[tuple[int, int], int] = {}
            is_off_for_rpdouble_const: dict[tuple[int, int], int] = {}

            for agent_id in ordered_agent_ids:
                for ci, day_date in enumerate(context_days):
                    key = (agent_id, day_date)
                    day_type_ctx = solver_input.existing_day_type_by_agent_day_ctx.get(key, DayType.REST.value)
                    in_window = ci in in_window_ctx_indices
                    if not in_window:
                        worked_day_const[(agent_id, ci)] = 1 if day_type_ctx in self.GPT_DAY_TYPES else 0
                        work_minutes_const[(agent_id, ci)] = solver_input.existing_work_minutes_by_agent_day_ctx.get(key, 0)
                        is_real_work_const[(agent_id, ci)] = 1 if day_type_ctx in self.REAL_WORK_DAY_TYPES_CONTEXT else 0
                        is_off_for_rpdouble_const[(agent_id, ci)] = 1 if day_type_ctx in self.RPDOUBLE_OFF_DAY_TYPES else 0
                        continue

                    di = date_to_index[day_date]
                    non_empty_vars = [
                        var
                        for (a, d, c), var in y.items()
                        if a == agent_id and d == di and combo_by_id[c].tranche_ids
                    ]
                    combo_work_expr = sum(
                        y[(agent_id, di, combo_id)] * combo_by_id[combo_id].work_minutes
                        for combo_id in combo_by_id
                        if (agent_id, di, combo_id) in y
                    )

                    real_work = model.NewBoolVar(f"is_real_work_a{agent_id}_c{ci}")
                    num_variables += 1
                    if non_empty_vars:
                        model.Add(real_work == sum(non_empty_vars))
                    else:
                        model.Add(real_work == 0)
                    num_constraints += 1
                    is_real_work_var[(agent_id, ci)] = real_work

                    worked_day = model.NewBoolVar(f"worked_day_a{agent_id}_c{ci}")
                    num_variables += 1
                    is_zcot = 1 if day_type_ctx == DayType.ZCOT.value else 0
                    is_leave_absent = 1 if day_type_ctx in {DayType.LEAVE.value, DayType.ABSENT.value} else 0
                    model.Add(worked_day >= real_work)
                    model.Add(worked_day >= is_zcot)
                    model.Add(worked_day >= is_leave_absent)
                    model.Add(worked_day <= real_work + is_zcot + is_leave_absent)
                    num_constraints += 4
                    worked_day_var[(agent_id, ci)] = worked_day

                    is_off_for_rpdouble = model.NewBoolVar(f"is_off_for_rpdouble_a{agent_id}_c{ci}")
                    num_variables += 1
                    model.Add(is_off_for_rpdouble == (1 if day_type_ctx in self.RPDOUBLE_OFF_DAY_TYPES else 0))
                    num_constraints += 1
                    is_off_for_rpdouble_var[(agent_id, ci)] = is_off_for_rpdouble

                    work_minutes = model.NewIntVar(0, 6000, f"work_minutes_a{agent_id}_c{ci}")
                    num_variables += 1
                    model.Add(work_minutes == combo_work_expr + (480 if is_zcot else 0))
                    num_constraints += 1
                    work_minutes_var[(agent_id, ci)] = work_minutes

            run_vars: dict[tuple[int, int, int], cp_model.IntVar] = {}
            N_ctx = len(context_days)

            def worked_expr(aid: int, idx: int):
                if (aid, idx) in worked_day_var:
                    return worked_day_var[(aid, idx)]
                return worked_day_const.get((aid, idx), 0)

            def real_work_expr(aid: int, idx: int):
                if (aid, idx) in is_real_work_var:
                    return is_real_work_var[(aid, idx)]
                return is_real_work_const.get((aid, idx), 0)

            def minutes_expr(aid: int, idx: int):
                if (aid, idx) in work_minutes_var:
                    return work_minutes_var[(aid, idx)]
                return work_minutes_const.get((aid, idx), 0)

            def off_for_rpdouble_expr(aid: int, idx: int):
                if (aid, idx) in is_off_for_rpdouble_var:
                    return is_off_for_rpdouble_var[(aid, idx)]
                return is_off_for_rpdouble_const.get((aid, idx), 0)

            for agent_id in ordered_agent_ids:
                for s in range(N_ctx):
                    for e in range(s, min(N_ctx, s + 6)):
                        L = e - s + 1
                        if L < 3:
                            continue
                        run = model.NewBoolVar(f"run_a{agent_id}_s{s}_e{e}")
                        num_variables += 1
                        run_vars[(agent_id, s, e)] = run
                        for i in range(s, e + 1):
                            model.Add(worked_expr(agent_id, i) == 1).OnlyEnforceIf(run)
                            num_constraints += 1
                        if s > 0:
                            model.Add(worked_expr(agent_id, s - 1) == 0).OnlyEnforceIf(run)
                            num_constraints += 1
                        if e < N_ctx - 1:
                            model.Add(worked_expr(agent_id, e + 1) == 0).OnlyEnforceIf(run)
                            num_constraints += 1

                        model.Add(sum(minutes_expr(agent_id, i) for i in range(s, e + 1)) <= 2880).OnlyEnforceIf(run)
                        num_constraints += 1

                        if L == 6:
                            if e + 2 >= N_ctx:
                                model.Add(run == 0)
                                num_constraints += 1
                            else:
                                model.Add(off_for_rpdouble_expr(agent_id, e + 1) == 1).OnlyEnforceIf(run)
                                num_constraints += 1
                                model.Add(off_for_rpdouble_expr(agent_id, e + 2) == 1).OnlyEnforceIf(run)
                                num_constraints += 1

                for i in range(N_ctx):
                    covering_runs = [
                        run
                        for (a, s, e), run in run_vars.items()
                        if a == agent_id and s <= i <= e
                    ]
                    model.Add(sum(covering_runs) == worked_expr(agent_id, i))
                    num_constraints += 1

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

            max_minutes = sum(combo.work_minutes for combo in combo_by_id.values())
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

            max_amplitude = sum(combo.amplitude_minutes for combo in combo_by_id.values())
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

        if amplitude_by_agent:
            model.Add(total_amplitude_cost == sum(amplitude_by_agent.values()))
        else:
            model.Add(total_amplitude_cost == 0)
        num_constraints += 1

        understaff_weighted_sum = model.NewIntVar(0, max(0, total_required_count * self.WEEKDAY_UNDERSTAFF_WEIGHT), "understaff_weighted_sum")
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

        # TODO(V2.2): penalize GPT lengths 3 and 6 for cleaner sequences.
        # TODO(V2.2): penalize primary tranche changes inside GPT sequences.
        # TODO(V2.2): add RP double bonus objective term.
        # TODO(V2.2): add fairness objective term by tranche_id distribution.
        objective = (
            self.W_COVER * understaff_weighted_sum
            + self.W_NIGHTS_TOTAL * total_night_days
            + self.W_NIGHTS_SPREAD * (max_nights - min_nights)
            + self.W_FAIR_MINUTES_SPREAD * (max_work_minutes - min_work_minutes)
            + self.W_FAIR_DAYS_SPREAD * (max_work_days - min_work_days)
            + self.W_AMPLITUDE * total_amplitude_cost
            + self.W_USELESS_WORK * useless_work_total
        )
        model.Minimize(objective)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = solver_input.time_limit_seconds
        solver.parameters.num_search_workers = 1
        if solver_input.seed is not None:
            solver.parameters.random_seed = solver_input.seed

        status = solver.Solve(model)
        wall_time = solver.WallTime()
        timeout_threshold = 0.99 * solver_input.time_limit_seconds
        is_timeout = bool(solver_input.time_limit_seconds > 0 and wall_time >= timeout_threshold)

        stats["solve_time_seconds"] = wall_time
        stats["num_variables"] = num_variables
        stats["num_constraints"] = num_constraints
        stats["coverage_constraints_count"] = coverage_constraints_count
        stats["num_rest_constraints"] = rest_constraints_count

        if status == cp_model.OPTIMAL:
            solver_status_raw = "OPTIMAL"
        elif status == cp_model.FEASIBLE:
            solver_status_raw = "FEASIBLE"
        elif status == cp_model.INFEASIBLE:
            solver_status_raw = "INFEASIBLE"
        elif status == cp_model.UNKNOWN:
            solver_status_raw = "UNKNOWN"
        else:
            solver_status_raw = "INFEASIBLE"

        normalized_solver_status = "TIMEOUT" if solver_status_raw == "UNKNOWN" and is_timeout else solver_status_raw
        stats["solver_status"] = solver_status_raw
        stats["solver_status_raw"] = solver_status_raw
        stats["normalized_solver_status"] = normalized_solver_status
        stats["is_timeout"] = is_timeout

        if status == cp_model.INFEASIBLE:
            raise InfeasibleError("infeasible", stats=stats)
        if status == cp_model.UNKNOWN and is_timeout:
            raise TimeoutError("timeout", stats=stats)
        if status == cp_model.UNKNOWN and not is_timeout:
            stats["timeout_confidence"] = "low"
            raise InfeasibleError("infeasible", stats=stats)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise InfeasibleError("infeasible", stats=stats)

        assignments: list[SolverAssignment] = []
        assigned_day_by_agent: set[tuple[int, int]] = set()
        for (agent_id, di, combo_id), var in y.items():
            if solver.Value(var) != 1:
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

        objective_value = solver.Value(objective)
        understaff_total = sum(solver.Value(var) for var in understaff_vars)
        understaff_total_weighted = solver.Value(understaff_weighted_sum)
        coverage_ratio = 1.0
        if total_required_count > 0:
            coverage_ratio = max(0.0, 1.0 - (understaff_total / total_required_count))
        coverage_ratio_weighted = 1.0
        if total_required_weighted > 0:
            coverage_ratio_weighted = max(0.0, 1.0 - (understaff_total_weighted / total_required_weighted))
        work_values = [solver.Value(work_days_by_agent[agent_id]) for agent_id in ordered_agent_ids]
        workload_min = min(work_values) if work_values else 0
        workload_max = max(work_values) if work_values else 0
        workload_avg = (sum(work_values) / len(work_values)) if work_values else 0.0

        combo_ids_used: set[int] = set()
        for (_agent_id, _di, combo_id), var in y.items():
            if solver.Value(var) == 1:
                combo_ids_used.add(combo_id)

        stats.update(
            {
                "solver_status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                "solver_status_raw": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                "normalized_solver_status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                "is_timeout": False,
                "score": objective_value,
                "objective_value": objective_value,
                "coverage_ratio": coverage_ratio,
                "understaff_total": understaff_total,
                "understaff_total_weighted": understaff_total_weighted,
                "coverage_ratio_weighted": coverage_ratio_weighted,
                "useless_work_total": solver.Value(useless_work_total),
                "num_combos_used_in_solution": len(combo_ids_used),
                "workload_min": workload_min,
                "workload_max": workload_max,
                "workload_avg": workload_avg,
                "max_work_days": solver.Value(max_work_days),
                "min_work_days": solver.Value(min_work_days),
                "nights_total": solver.Value(total_night_days),
                "nights_min": solver.Value(min_nights),
                "nights_max": solver.Value(max_nights),
                "amplitude_cost_total": solver.Value(total_amplitude_cost),
                "objective_terms": {
                    "understaff_weighted": understaff_total_weighted,
                    "nights_total": solver.Value(total_night_days),
                    "nights_spread": solver.Value(max_nights) - solver.Value(min_nights),
                    "fair_minutes_spread": solver.Value(max_work_minutes) - solver.Value(min_work_minutes),
                    "fair_days_spread": solver.Value(max_work_days) - solver.Value(min_work_days),
                    "amplitude_cost": solver.Value(total_amplitude_cost),
                    "useless_work": solver.Value(useless_work_total),
                },
                "num_assignments": len(assignments),
            }
        )

        return SolverOutput(
            agent_days=agent_days,
            assignments=assignments,
            stats=stats,
        )
