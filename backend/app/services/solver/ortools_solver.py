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
        tranches_by_id = {tranche.id: tranche for tranche in solver_input.tranches}

        demanded_tranche_ids_by_date_idx: dict[int, set[int]] = {}
        for demand in solver_input.coverage_demands:
            di = date_to_index[demand.day_date]
            demanded_tranche_ids_by_date_idx.setdefault(di, set()).add(demand.tranche_id)
        demanded_pairs_count = sum(len(tranche_ids) for tranche_ids in demanded_tranche_ids_by_date_idx.values())

        x: dict[tuple[int, int, int], cp_model.IntVar] = {}
        vars_by_agent_day: dict[tuple[int, int], list[cp_model.IntVar]] = {}
        vars_by_demand: dict[tuple[int, int], list[cp_model.IntVar]] = {}

        for agent_id in ordered_agent_ids:
            for di, day_date in enumerate(dates):
                if (agent_id, day_date) in solver_input.absences:
                    continue

                demanded_tranches_for_day = demanded_tranche_ids_by_date_idx.get(di, set())
                for tranche_id in demanded_tranches_for_day:
                    tranche = tranches_by_id.get(tranche_id)
                    if tranche is None:
                        continue
                    if tranche.poste_id not in qual_posts.get(agent_id, set()):
                        continue
                    min_qual_date = qual_date.get((agent_id, tranche.poste_id))
                    if min_qual_date is not None and day_date < min_qual_date:
                        continue

                    var = model.NewBoolVar(f"x_a{agent_id}_d{di}_t{tranche.id}")
                    x[(agent_id, di, tranche.id)] = var
                    vars_by_agent_day.setdefault((agent_id, di), []).append(var)
                    vars_by_demand.setdefault((di, tranche.id), []).append(var)

        for agent_id in ordered_agent_ids:
            for di in range(len(dates)):
                day_vars = vars_by_agent_day.get((agent_id, di), [])
                if day_vars:
                    model.Add(sum(day_vars) <= 1)
                    num_constraints += 1

        for demand in solver_input.coverage_demands:
            di = date_to_index[demand.day_date]
            demand_vars = vars_by_demand.get((di, demand.tranche_id), [])
            if len(demand_vars) < demand.required_count:
                raise InfeasibleError("not enough available qualified agents")
            model.Add(sum(demand_vars) == demand.required_count)
            num_constraints += 1

        work_days_by_agent: dict[int, cp_model.IntVar] = {}
        for agent_id in ordered_agent_ids:
            vars_for_agent = [var for (a, _di, _t), var in x.items() if a == agent_id]
            work_days = model.NewIntVar(0, len(dates), f"work_days_a{agent_id}")
            if vars_for_agent:
                model.Add(work_days == sum(vars_for_agent))
            else:
                model.Add(work_days == 0)
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
        for (agent_id, di, tranche_id), var in x.items():
            if solver.Value(var) == 1:
                assignments.append(SolverAssignment(agent_id=agent_id, day_date=dates[di], tranche_id=tranche_id))
                assigned_day_by_agent.add((agent_id, di))

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
                "num_variables": len(x),
                "num_constraints": num_constraints,
                "demanded_pairs_count": demanded_pairs_count,
                "workload_min": workload_min,
                "workload_max": workload_max,
                "workload_avg": workload_avg,
                "max_work_days": solver.Value(max_work_days),
                "min_work_days": solver.Value(min_work_days),
                "num_assignments": len(assignments),
            },
        )
