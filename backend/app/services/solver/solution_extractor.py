from __future__ import annotations

from datetime import date
from typing import Any

from core.domain.enums.day_type import DayType

from backend.app.services.solver.models import SolverAgentDay, SolverAssignment, SolverInput


def extract_solution(
    *,
    eval_solver: Any,
    y: dict[tuple[int, int, int], Any],
    combo_by_id: dict[int, Any],
    dates: list[Any],
    date_to_index: dict[Any, int],
    ordered_agent_ids: list[int],
    solver_input: SolverInput,
    hard_daytype_overrides: dict[tuple[int, date], str] | None = None,
) -> tuple[list[SolverAssignment], list[SolverAgentDay], set[tuple[int, int]]]:
    """Extract assignments and agent-day statuses from solved CP-SAT variables.

    Extraction-only utility: does not mutate flat/grouped stats.
    """
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

    overrides = hard_daytype_overrides or {}
    assignments = [
        assignment
        for assignment in assignments
        if overrides.get((assignment.agent_id, assignment.day_date)) not in {DayType.ABSENT.value, DayType.LEAVE.value}
    ]
    assignments.sort(key=lambda item: (item.day_date, item.agent_id, item.tranche_id))

    agent_days: list[SolverAgentDay] = []
    for day_date in dates:
        di = date_to_index[day_date]
        for agent_id in ordered_agent_ids:
            override_day_type = overrides.get((agent_id, day_date))
            if override_day_type is not None:
                day_type = override_day_type
            elif (agent_id, di) in assigned_day_by_agent:
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
    return assignments, agent_days, assigned_day_by_agent
