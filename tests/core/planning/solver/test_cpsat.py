from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import pytest

pytestmark = [pytest.mark.unit, pytest.mark.planning]

from core.planning.solver.cpsat import solve_planning
from core.planning.solver.models import (
    BaselineGroup,
    LockType,
    Need,
    PlanningInstance,
    PlanningMode,
    SlotLock,
    SolverAgent,
)
from core.planning.solver.extractors import expand_needs_to_slots
from core.planning.solver.params import SolverParams


def _instance_plan(*, needs: list[Need], agents: list[SolverAgent], locks=None) -> PlanningInstance:
    slots = expand_needs_to_slots(needs)
    return PlanningInstance(
        agents=agents,
        slots=slots,
        baseline_groups=[],
        locks=locks or [],
        mode=PlanningMode.PLAN,
    )


def test_plan_covers_slots_when_possible():
    needs = [
        Need(poste_id=1, date=date(2026, 2, 20), tranche_id=10, required_count=1),
        Need(poste_id=1, date=date(2026, 2, 21), tranche_id=10, required_count=1),
    ]
    agents = [
        SolverAgent(id=1, qualifications={1}, unavailable_dates=set()),
    ]
    inst = _instance_plan(needs=needs, agents=agents)

    sol = solve_planning(inst, params=SolverParams(time_limit_s=2.0, max_consecutive_days=None))
    assert sol.status in {"OPTIMAL", "FEASIBLE"}
    assert sol.uncovered_slot_ids == []


def test_unavailability_blocks_assignment():
    needs = [Need(poste_id=1, date=date(2026, 2, 20), tranche_id=10, required_count=1)]
    agents = [
        SolverAgent(id=1, qualifications={1}, unavailable_dates={date(2026, 2, 20)}),
    ]
    inst = _instance_plan(needs=needs, agents=agents)

    sol = solve_planning(inst, params=SolverParams(time_limit_s=2.0, max_consecutive_days=None))
    assert sol.status in {"OPTIMAL", "FEASIBLE"}
    assert sol.uncovered_slot_ids == [0]  # slot 0 non couvert


def test_one_slot_per_day_per_agent():
    # 2 slots même jour, 1 agent => 1 couvert, 1 uncovered
    needs = [Need(poste_id=1, date=date(2026, 2, 20), tranche_id=10, required_count=2)]
    agents = [SolverAgent(id=1, qualifications={1}, unavailable_dates=set())]
    inst = _instance_plan(needs=needs, agents=agents)

    sol = solve_planning(inst, params=SolverParams(time_limit_s=2.0, max_consecutive_days=None))
    assert sol.status in {"OPTIMAL", "FEASIBLE"}
    assert len(sol.uncovered_slot_ids) == 1
    assert len(sol.assignments) == 1


def test_hard_lock_is_enforced():
    needs = [Need(poste_id=1, date=date(2026, 2, 20), tranche_id=10, required_count=1)]
    agents = [
        SolverAgent(id=1, qualifications={1}, unavailable_dates=set()),
        SolverAgent(id=2, qualifications={1}, unavailable_dates=set()),
    ]
    slots = expand_needs_to_slots(needs)
    locks = [SlotLock(slot_id=slots[0].id, lock_type=LockType.HARD, agent_id=2)]

    inst = PlanningInstance(
        agents=agents,
        slots=slots,
        baseline_groups=[],
        locks=locks,
        mode=PlanningMode.PLAN,
    )

    sol = solve_planning(inst, params=SolverParams(time_limit_s=2.0, max_consecutive_days=None))
    assert sol.status in {"OPTIMAL", "FEASIBLE"}
    assert sol.uncovered_slot_ids == []
    assert sol.assignments == [(2, 0)]


def test_repair_change_count_prefers_keep_baseline():
    # Baseline A,B sur (poste=1, date=20, tranche=10), besoin=2 slots.
    # Agents A,B,C qualifiés.
    # Le solveur doit garder A,B (change_count=0) plutôt que A,C (change_count=1).
    needs = [Need(poste_id=1, date=date(2026, 2, 20), tranche_id=10, required_count=2)]
    slots = expand_needs_to_slots(needs)

    agents = [
        SolverAgent(id=1, qualifications={1}, unavailable_dates=set()),
        SolverAgent(id=2, qualifications={1}, unavailable_dates=set()),
        SolverAgent(id=3, qualifications={1}, unavailable_dates=set()),
    ]

    baseline_groups = [
        BaselineGroup(poste_id=1, date=date(2026, 2, 20), tranche_id=10, agents={1, 2})
    ]

    inst = PlanningInstance(
        agents=agents,
        slots=slots,
        baseline_groups=baseline_groups,
        locks=[],  # pas de HARD
        mode=PlanningMode.REPAIR,
    )

    sol = solve_planning(inst, params=SolverParams(time_limit_s=2.0, max_consecutive_days=None))
    assert sol.status in {"OPTIMAL", "FEASIBLE"}
    assert sol.uncovered_slot_ids == []
    # change_count doit être 0
    assert sol.change_count_by_group[(1, date(2026, 2, 20), 10)] == 0
    assert set(a for a, _ in sol.assignments) == {1, 2}
