from __future__ import annotations

from dataclasses import dataclass
from ortools.sat.python import cp_model

from backend.app.services.solver.rh_combos import DayCombo


@dataclass
class ChoiceVarsBuildResult:
    y: dict[tuple[int, int, int], cp_model.IntVar]
    vars_by_agent_day: dict[tuple[int, int], list[cp_model.IntVar]]
    vars_by_demand: dict[tuple[int, int], list[cp_model.IntVar]]
    var_to_key: dict[int, tuple[int, int, int]]
    combo_ids_in_model: set[int]
    combo_candidate_pairs_count: int
    combo_allowed_pairs_count: int
    combo_rejected_absence_count: int
    combo_rejected_not_qualified_count: int
    combo_rejected_qualification_date_count: int
    combo_rejected_unknown_daytype_forces_rest_count: int
    combo_rejected_other_count: int
    combo_rejected_samples: list[dict]
    combo_allowed_samples: list[dict]
    y_variables_count: int
    num_variables_delta: int
    num_constraints_delta: int


def build_choice_vars_and_samples(*, model: cp_model.CpModel, ordered_agent_ids: list[int], dates: list, solver_absences: set[tuple[int, object]], sorted_work_combos: list[DayCombo], qual_posts: dict[int, set[int]], qual_date: dict[tuple[int, int], object],) -> ChoiceVarsBuildResult:
    y = {}
    vars_by_agent_day = {}
    vars_by_demand = {}
    var_to_key = {}
    combo_candidate_pairs_count = 0
    combo_allowed_pairs_count = 0
    combo_rejected_absence_count = 0
    combo_rejected_not_qualified_count = 0
    combo_rejected_qualification_date_count = 0
    combo_rejected_unknown_daytype_forces_rest_count = 0
    combo_rejected_other_count = 0
    combo_rejected_samples = []
    combo_allowed_samples = []
    y_variables_count = 0
    combo_ids_in_model: set[int] = set()
    num_variables = 0
    num_constraints = 0

    def _append_sample(samples: list[dict], *, agent_id: int, day_date, combo_id: int, poste_id: int | None, reason: str) -> None:
        if len(samples) >= 10:
            return
        samples.append({"agent_id": agent_id, "day_date": day_date.isoformat(), "combo_id": combo_id, "poste_id": poste_id, "reason": reason})

    for agent_id in ordered_agent_ids:
        for di, day_date in enumerate(dates):
            is_absent = (agent_id, day_date) in solver_absences
            var = model.NewBoolVar(f"y_a{agent_id}_d{di}_c0")
            num_variables += 1
            y_variables_count += 1
            y[(agent_id, di, 0)] = var
            var_to_key[id(var)] = (agent_id, di, 0)
            combo_ids_in_model.add(0)
            vars_by_agent_day.setdefault((agent_id, di), []).append(var)
            if is_absent:
                model.Add(var == 1)
                num_constraints += 1

            for combo in sorted_work_combos:
                combo_candidate_pairs_count += 1
                combo_id = combo.id
                reason = None
                if is_absent:
                    combo_rejected_absence_count += 1
                    reason = "absence"
                elif combo.poste_id is None:
                    pass
                elif combo.poste_id not in qual_posts.get(agent_id, set()):
                    combo_rejected_not_qualified_count += 1
                    reason = "not_qualified"
                else:
                    min_qual_date = qual_date.get((agent_id, combo.poste_id))
                    if min_qual_date is not None and day_date < min_qual_date:
                        combo_rejected_qualification_date_count += 1
                        reason = "qualification_date"

                if reason is not None:
                    _append_sample(combo_rejected_samples, agent_id=agent_id, day_date=day_date, combo_id=combo_id, poste_id=combo.poste_id, reason=reason)
                    continue

                combo_allowed_pairs_count += 1
                _append_sample(combo_allowed_samples, agent_id=agent_id, day_date=day_date, combo_id=combo_id, poste_id=combo.poste_id, reason="allowed")
                var = model.NewBoolVar(f"y_a{agent_id}_d{di}_c{combo_id}")
                num_variables += 1
                y_variables_count += 1
                y[(agent_id, di, combo_id)] = var
                var_to_key[id(var)] = (agent_id, di, combo_id)
                combo_ids_in_model.add(combo_id)
                vars_by_agent_day.setdefault((agent_id, di), []).append(var)
                for tranche_id in combo.tranche_ids:
                    vars_by_demand.setdefault((di, tranche_id), []).append(var)

    return ChoiceVarsBuildResult(
        y=y,
        vars_by_agent_day=vars_by_agent_day,
        vars_by_demand=vars_by_demand,
        var_to_key=var_to_key,
        combo_ids_in_model=combo_ids_in_model,
        combo_candidate_pairs_count=combo_candidate_pairs_count,
        combo_allowed_pairs_count=combo_allowed_pairs_count,
        combo_rejected_absence_count=combo_rejected_absence_count,
        combo_rejected_not_qualified_count=combo_rejected_not_qualified_count,
        combo_rejected_qualification_date_count=combo_rejected_qualification_date_count,
        combo_rejected_unknown_daytype_forces_rest_count=combo_rejected_unknown_daytype_forces_rest_count,
        combo_rejected_other_count=combo_rejected_other_count,
        combo_rejected_samples=combo_rejected_samples,
        combo_allowed_samples=combo_allowed_samples,
        y_variables_count=y_variables_count,
        num_variables_delta=num_variables,
        num_constraints_delta=num_constraints,
    )


def add_daily_choice_constraints(*, model: cp_model.CpModel, ordered_agent_ids: list[int], dates: list, vars_by_agent_day: dict[tuple[int, int], list[cp_model.IntVar]]) -> int:
    num_constraints = 0
    for agent_id in ordered_agent_ids:
        for di in range(len(dates)):
            day_vars = vars_by_agent_day.get((agent_id, di), [])
            if day_vars:
                model.Add(sum(day_vars) == 1)
                num_constraints += 1
    return num_constraints


def add_rest_compat_constraints(*, model: cp_model.CpModel, y: dict[tuple[int, int, int], cp_model.IntVar], ordered_agent_ids: list[int], dates: list, combo_ids: list[int], compatible_pairs: set[tuple[int, int]]) -> tuple[int, int]:
    num_constraints = 0
    rest_constraints_count = 0
    compatible_by_prev = {c1: set() for c1 in combo_ids}
    for c1, c2 in compatible_pairs:
        compatible_by_prev.setdefault(c1, set()).add(c2)

    for agent_id in ordered_agent_ids:
        for di in range(1, len(dates)):
            prev_combo_ids = [cid for (a, d, cid) in y if a == agent_id and d == di - 1]
            curr_combo_ids = [cid for (a, d, cid) in y if a == agent_id and d == di]
            curr_set = set(curr_combo_ids)
            for c1 in prev_combo_ids:
                for c2 in curr_set - compatible_by_prev.get(c1, set()):
                    prev_var = y.get((agent_id, di - 1, c1))
                    curr_var = y.get((agent_id, di, c2))
                    if prev_var is None or curr_var is None:
                        continue
                    model.Add(prev_var + curr_var <= 1)
                    num_constraints += 1
                    rest_constraints_count += 1
    return num_constraints, rest_constraints_count


def build_prioritized_decision_vars(*, coverage_demands: list, date_to_index: dict, dates: list, tranche_by_id: dict[int, object], vars_by_demand: dict[tuple[int, int], list[cp_model.IntVar]], var_to_key: dict[int, tuple[int, int, int]], max_vars: int = 5000,) -> tuple[list[tuple[int, int]], list[cp_model.IntVar]]:
    required_by_day: dict[int, int] = {}
    for demand in coverage_demands:
        di = date_to_index[demand.day_date]
        required_by_day[di] = required_by_day.get(di, 0) + max(0, demand.required_count)
    day_scores = sorted(required_by_day.items(), key=lambda item: (-item[1], dates[item[0]]))

    prioritized_y: list[cp_model.IntVar] = []
    seen_ids: set[int] = set()
    for di, _score in day_scores:
        demand_triplets = []
        for demand in coverage_demands:
            ddi = date_to_index[demand.day_date]
            if ddi != di:
                continue
            demand_triplets.append((int(demand.poste_id or tranche_by_id[demand.tranche_id].poste_id), int(demand.tranche_id), vars_by_demand.get((ddi, demand.tranche_id), [])))
        demand_triplets.sort(key=lambda x: (x[0], x[1]))
        for _poste_id, _tranche_id, dvars in demand_triplets:
            keys_for_vars = []
            for v in dvars:
                key = var_to_key.get(id(v))
                if key is None:
                    continue
                aid, _di, cid = key
                keys_for_vars.append((aid, cid, v))
            keys_for_vars.sort(key=lambda t: (t[0], t[1]))
            for _aid, _cid, v in keys_for_vars:
                vid = id(v)
                if vid in seen_ids:
                    continue
                seen_ids.add(vid)
                prioritized_y.append(v)
                if len(prioritized_y) >= max_vars:
                    break
            if len(prioritized_y) >= max_vars:
                break
        if len(prioritized_y) >= max_vars:
            break
    return day_scores, prioritized_y
