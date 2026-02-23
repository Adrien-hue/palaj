from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model

from .models import BaselineGroup, LockType, PlanningInstance, PlanningMode, SolverSlot
from .params import SolverParams, weights_for_mode
from .solution import GroupKey, PlanningSolution


def _status_to_str(status: int) -> str:
    if status == cp_model.OPTIMAL:
        return "OPTIMAL"
    if status == cp_model.FEASIBLE:
        return "FEASIBLE"
    if status == cp_model.INFEASIBLE:
        return "INFEASIBLE"
    if status == cp_model.MODEL_INVALID:
        return "MODEL_INVALID"
    return f"UNKNOWN({status})"


def solve_planning(
    instance: PlanningInstance,
    *,
    params: SolverParams | None = None,
) -> PlanningSolution:
    params = params or SolverParams()

    model = cp_model.CpModel()

    P_uncovered, P_change = weights_for_mode(instance.mode)

    # ----- Index helpers -----
    agents = instance.agents
    slots = instance.slots

    agent_ids = [a.id for a in agents]
    agent_by_id = {a.id: a for a in agents}
    slot_by_id = {s.id: s for s in slots}
    slot_key_by_id: Dict[int, GroupKey] = {s.id: s.key for s in slots}

    # Group slots by date for 1-slot/day constraint
    slots_by_date: Dict[date, List[SolverSlot]] = defaultdict(list)
    for s in slots:
        slots_by_date[s.date].append(s)

    # ----- Variables -----
    # x[(agent_id, slot_id)] = BoolVar only if allowed by qualification+availability
    x: Dict[Tuple[int, int], cp_model.IntVar] = {}

    for s in slots:
        for aid in agent_ids:
            a = agent_by_id[aid]
            # qualification: poste_id must be in agent.qualifications
            if s.poste_id not in a.qualifications:
                continue
            # unavailability: date in unavailable_dates => forbidden
            if s.date in a.unavailable_dates:
                continue
            x[(aid, s.id)] = model.NewBoolVar(f"x_a{aid}_s{s.id}")

    uncovered: Dict[int, cp_model.IntVar] = {
        s.id: model.NewBoolVar(f"uncovered_s{s.id}") for s in slots
    }

    # ----- Hard locks -----
    hard_lock_agent_by_slot: Dict[int, int] = {}
    for lk in instance.locks:
        if lk.lock_type == LockType.HARD:
            if lk.agent_id is None:
                raise ValueError("HARD lock requires agent_id")
            hard_lock_agent_by_slot[int(lk.slot_id)] = int(lk.agent_id)

    # ----- Constraints -----
    # Coverage per slot: sum_a x[a,s] + uncovered[s] == 1
    for s in slots:
        vars_for_slot = [var for (aid, sid), var in x.items() if sid == s.id]
        # If hard lock exists, force it (and remove uncovered)
        if s.id in hard_lock_agent_by_slot:
            aid = hard_lock_agent_by_slot[s.id]
            # If the (aid,s) var wasn't created due to qualif/indispo, it's inconsistent data
            if (aid, s.id) not in x:
                raise ValueError(
                    f"HARD lock impossible: agent {aid} cannot take slot {s.id} "
                    f"(poste={s.poste_id}, date={s.date})"
                )
            model.Add(x[(aid, s.id)] == 1)
            model.Add(uncovered[s.id] == 0)
            # Any other x[a,s] must be 0 (if they exist)
            for (aid2, sid2), var in x.items():
                if sid2 == s.id and aid2 != aid:
                    model.Add(var == 0)
            continue

        model.Add(sum(vars_for_slot) + uncovered[s.id] == 1)

    # At most 1 slot/day/agent
    for aid in agent_ids:
        for d, dslots in slots_by_date.items():
            vars_for_day = [x[(aid, s.id)] for s in dslots if (aid, s.id) in x]
            if vars_for_day:
                model.Add(sum(vars_for_day) <= 1)

    # Max consecutive working days (generic v1): count a day worked if any slot assigned that day
    if params.max_consecutive_days is not None:
        K = int(params.max_consecutive_days)
        if K < 1:
            raise ValueError("max_consecutive_days must be >= 1 or None")

        all_dates = sorted(slots_by_date.keys())
        if all_dates:
            dmin, dmax = all_dates[0], all_dates[-1]
            horizon = (dmax - dmin).days + 1
            ordered_dates = [dmin + timedelta(days=i) for i in range(horizon)]

            # worked[a,d] as BoolVar (sum x <=1 already, so we can equate)
            worked: Dict[Tuple[int, date], cp_model.IntVar] = {}
            for aid in agent_ids:
                for d in ordered_dates:
                    v = model.NewBoolVar(f"worked_a{aid}_{d.isoformat()}")
                    day_vars = [x[(aid, s.id)] for s in slots_by_date.get(d, []) if (aid, s.id) in x]
                    if day_vars:
                        model.Add(sum(day_vars) == v)
                    else:
                        model.Add(v == 0)
                    worked[(aid, d)] = v

                # Sliding window of size K+1: sum worked <= K
                if len(ordered_dates) >= K + 1:
                    for i in range(0, len(ordered_dates) - (K + 1) + 1):
                        window = ordered_dates[i : i + (K + 1)]
                        model.Add(sum(worked[(aid, wd)] for wd in window) <= K)

    # ----- REPAIR: change_count by group -----
    change_count_by_group_var: Dict[GroupKey, cp_model.IntVar] = {}
    if instance.mode == PlanningMode.REPAIR and instance.baseline_groups:
        # Map group -> list of slot_ids in that group
        slots_in_group: Dict[GroupKey, List[int]] = defaultdict(list)
        for s in slots:
            slots_in_group[s.key].append(s.id)

        for g in instance.baseline_groups:
            key = g.key
            baseline_agents = sorted(g.agents)

            # For each baseline agent, assigned[a,g] = OR_{s in group} x[a,s]
            assigned_ag: Dict[int, cp_model.IntVar] = {}
            removed_ag: Dict[int, cp_model.IntVar] = {}

            for aid in baseline_agents:
                av = model.NewBoolVar(f"assigned_a{aid}_g{key[0]}_{key[1].isoformat()}_{key[2]}")
                assigned_ag[aid] = av

                relevant = [x[(aid, sid)] for sid in slots_in_group.get(key, []) if (aid, sid) in x]
                if relevant:
                    model.AddMaxEquality(av, relevant)
                else:
                    model.Add(av == 0)

                rv = model.NewBoolVar(f"removed_a{aid}_g{key[0]}_{key[1].isoformat()}_{key[2]}")
                removed_ag[aid] = rv
                model.Add(rv + av == 1)

            cc = model.NewIntVar(0, len(baseline_agents), f"change_count_g{key[0]}_{key[1].isoformat()}_{key[2]}")
            model.Add(cc == sum(removed_ag.values()) if removed_ag else 0)
            change_count_by_group_var[key] = cc

    # ----- Objective -----
    uncovered_cost = sum(P_uncovered * uncovered[sid] for sid in uncovered)
    change_cost = 0
    if change_count_by_group_var:
        change_cost = sum(P_change * v for v in change_count_by_group_var.values())

    model.Minimize(uncovered_cost + change_cost)

    # ----- Solve -----
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(params.time_limit_s)
    if params.num_workers is not None:
        solver.parameters.num_search_workers = int(params.num_workers)
    if params.enable_log:
        solver.parameters.log_search_progress = True

    status = solver.Solve(model)
    status_str = _status_to_str(status)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignments: List[Tuple[int, int]] = []
        for (aid, sid), var in x.items():
            if solver.Value(var) == 1:
                assignments.append((aid, sid))
        assignments.sort(key=lambda t: (t[1], t[0]))  # stable

        uncovered_slot_ids = [sid for sid, var in uncovered.items() if solver.Value(var) == 1]
        uncovered_slot_ids.sort()

        change_count_by_group: Dict[GroupKey, int] = {}
        for key, v in change_count_by_group_var.items():
            change_count_by_group[key] = int(solver.Value(v))

        return PlanningSolution(
            status=status_str,
            objective_value=int(solver.ObjectiveValue()),
            assignments=assignments,
            uncovered_slot_ids=uncovered_slot_ids,
            change_count_by_group=change_count_by_group,
        )

    # INFEASIBLE / MODEL_INVALID etc.
    return PlanningSolution(
        status=status_str,
        objective_value=0,
        assignments=[],
        uncovered_slot_ids=[],
        change_count_by_group={},
    )
