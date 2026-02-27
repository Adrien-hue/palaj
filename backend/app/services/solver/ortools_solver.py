from __future__ import annotations

from datetime import timedelta

from ortools.sat.python import cp_model

from core.domain.enums.day_type import DayType

from .models import (
    InfeasibleError,
    SolverAgentDay,
    SolverAssignment,
    SolverInput,
    SolverOutput,
    TimeoutError,
)
from .rh_combos import DayCombo, DefaultRhComboRulesEngine, build_day_combos_for_poste, build_rest_compatibility


class OrtoolsSolver:
    def generate(self, solver_input: SolverInput) -> SolverOutput:
        model = cp_model.CpModel()
        num_constraints = 0

        ordered_agent_ids = sorted(solver_input.agent_ids)
        dates: list = []
        cursor = solver_input.start_date
        while cursor <= solver_input.end_date:
            dates.append(cursor)
            cursor += timedelta(days=1)
        date_to_index = {d: i for i, d in enumerate(dates)}

        qual_posts = {agent_id: set(postes) for agent_id, postes in solver_input.qualified_postes_by_agent.items()}
        qual_date = solver_input.qualification_date_by_agent_poste

        demanded_tranche_ids_by_date_idx: dict[int, set[int]] = {}
        for demand in solver_input.coverage_demands:
            di = date_to_index[demand.day_date]
            demanded_tranche_ids_by_date_idx.setdefault(di, set()).add(demand.tranche_id)
        demanded_pairs_count = sum(len(tranche_ids) for tranche_ids in demanded_tranche_ids_by_date_idx.values())

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
        combo_ids_by_poste: dict[int, list[int]] = {}
        for combo in combos:
            if combo.poste_id is not None:
                combo_ids_by_poste.setdefault(combo.poste_id, []).append(combo.id)

        compatible_pairs = build_rest_compatibility(combos=combos, rh_engine=rh_engine)

        y: dict[tuple[int, int, int], cp_model.IntVar] = {}
        vars_by_agent_day: dict[tuple[int, int], list[cp_model.IntVar]] = {}
        vars_by_demand: dict[tuple[int, int], list[cp_model.IntVar]] = {}

        for agent_id in ordered_agent_ids:
            for di, day_date in enumerate(dates):
                key = (agent_id, day_date)
                if key in solver_input.absences:
                    var = model.NewBoolVar(f"y_a{agent_id}_d{di}_c0")
                    y[(agent_id, di, 0)] = var
                    vars_by_agent_day.setdefault((agent_id, di), []).append(var)
                    model.Add(var == 1)
                    num_constraints += 1
                    continue

                allowed_combo_ids = {0}
                for poste_id in qual_posts.get(agent_id, set()):
                    min_qual_date = qual_date.get((agent_id, poste_id))
                    if min_qual_date is not None and day_date < min_qual_date:
                        continue
                    allowed_combo_ids.update(combo_ids_by_poste.get(poste_id, []))

                for combo_id in sorted(allowed_combo_ids):
                    var = model.NewBoolVar(f"y_a{agent_id}_d{di}_c{combo_id}")
                    y[(agent_id, di, combo_id)] = var
                    vars_by_agent_day.setdefault((agent_id, di), []).append(var)
                    combo = combo_by_id[combo_id]
                    for tranche_id in combo.tranche_ids:
                        vars_by_demand.setdefault((di, tranche_id), []).append(var)

        for agent_id in ordered_agent_ids:
            for di in range(len(dates)):
                day_vars = vars_by_agent_day.get((agent_id, di), [])
                if day_vars:
                    model.Add(sum(day_vars) == 1)
                    num_constraints += 1

        # Coverage constraints are built strictly from explicit demands only.
        # No implicit zero-demand constraints should be added for non-demanded (day, tranche) pairs.
        coverage_constraints_count = 0
        for demand in solver_input.coverage_demands:
            di = date_to_index[demand.day_date]
            demand_vars = vars_by_demand.get((di, demand.tranche_id), [])
            if len(demand_vars) < demand.required_count:
                raise InfeasibleError("not enough available qualified agents")
            model.Add(sum(demand_vars) == demand.required_count)
            num_constraints += 1
            coverage_constraints_count += 1

        incompatible_pairs = {(c1, c2) for c1 in combo_by_id for c2 in combo_by_id if (c1, c2) not in compatible_pairs}
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

        work_days_by_agent: dict[int, cp_model.IntVar] = {}
        for agent_id in ordered_agent_ids:
            work_day_vars: list[cp_model.IntVar] = []
            for di in range(len(dates)):
                non_empty_vars = [
                    var
                    for (a, d, c), var in y.items()
                    if a == agent_id and d == di and combo_by_id[c].tranche_ids
                ]
                work_day = model.NewIntVar(0, 1, f"work_day_a{agent_id}_d{di}")
                if non_empty_vars:
                    model.Add(work_day == sum(non_empty_vars))
                else:
                    model.Add(work_day == 0)
                num_constraints += 1
                work_day_vars.append(work_day)

            work_days = model.NewIntVar(0, len(dates), f"work_days_a{agent_id}")
            model.Add(work_days == sum(work_day_vars))
            num_constraints += 1
            work_days_by_agent[agent_id] = work_days

        max_work_days = model.NewIntVar(0, len(dates), "max_work_days")
        min_work_days = model.NewIntVar(0, len(dates), "min_work_days")
        if work_days_by_agent:
            model.AddMaxEquality(max_work_days, list(work_days_by_agent.values()))
            model.AddMinEquality(min_work_days, list(work_days_by_agent.values()))
            num_constraints += 2
        else:
            model.Add(max_work_days == 0)
            model.Add(min_work_days == 0)
            num_constraints += 2

        objective = max_work_days - min_work_days
        model.Minimize(objective)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = solver_input.time_limit_seconds
        solver.parameters.num_search_workers = 1
        if solver_input.seed is not None:
            solver.parameters.random_seed = solver_input.seed

        status = solver.Solve(model)
        if status == cp_model.INFEASIBLE:
            raise InfeasibleError("infeasible")
        if status == cp_model.UNKNOWN:
            raise TimeoutError("timeout")
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise InfeasibleError("infeasible")

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
        work_values = [solver.Value(work_days_by_agent[agent_id]) for agent_id in ordered_agent_ids]
        workload_min = min(work_values) if work_values else 0
        workload_max = max(work_values) if work_values else 0
        workload_avg = (sum(work_values) / len(work_values)) if work_values else 0.0

        num_combos_effective = len({combo_id for (_a, _d, combo_id) in y.keys()})

        return SolverOutput(
            agent_days=agent_days,
            assignments=assignments,
            stats={
                "solver_status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                "score": objective_value,
                "objective_value": objective_value,
                "coverage_ratio": 1.0,
                "soft_violations": 0,
                "solve_time_seconds": solver.WallTime(),
                "num_variables": len(y),
                "num_constraints": num_constraints,
                "demanded_pairs_count": demanded_pairs_count,
                "coverage_constraints_count": coverage_constraints_count,
                "num_combos_total": len(combos),
                "num_combos_effective": num_combos_effective,
                "num_incompatible_pairs": len(incompatible_pairs),
                "num_rest_constraints": rest_constraints_count,
                "workload_min": workload_min,
                "workload_max": workload_max,
                "workload_avg": workload_avg,
                "max_work_days": solver.Value(max_work_days),
                "min_work_days": solver.Value(min_work_days),
                "num_assignments": len(assignments),
            },
        )
