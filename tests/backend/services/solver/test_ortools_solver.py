from __future__ import annotations

from datetime import date

import pytest

from backend.app.services.solver.models import (
    CoverageDemand,
    InfeasibleError,
    SolverInput,
    TimeoutError,
    TrancheInfo,
)
from backend.app.services.solver.ortools_solver import OrtoolsSolver


def _build_input(**kwargs) -> SolverInput:
    base = dict(
        team_id=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 2),
        seed=123,
        time_limit_seconds=5,
        agent_ids=[1, 2],
        absences=set(),
        qualified_postes_by_agent={1: (1,), 2: (1,)},
        qualification_date_by_agent_poste={(1, 1): None, (2, 1): None},
        existing_day_type_by_agent_day={},
        poste_ids=[1],
        tranches=[TrancheInfo(id=10, poste_id=1)],
        coverage_demands=[],
    )
    base.update(kwargs)
    return SolverInput(**base)


def test_feasible_respects_qualification_date():
    solver = OrtoolsSolver()
    inp = _build_input(
        qualification_date_by_agent_poste={(1, 1): None, (2, 1): date(2026, 1, 2)},
        coverage_demands=[
            CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1),
            CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
        ],
    )

    out = solver.generate(inp)

    day1_assignments = [a for a in out.assignments if a.day_date == date(2026, 1, 1)]
    assert len(day1_assignments) == 1
    assert day1_assignments[0].agent_id == 1
    assert out.stats["coverage_ratio"] == 1.0
    assert out.stats["num_variables"] > 0
    assert out.stats["solve_time_seconds"] >= 0
    assert out.stats["objective_value"] == out.stats["score"]
    assert out.stats["num_constraints"] >= 0
    assert out.stats["demanded_pairs_count"] == 2


def test_infeasible_when_required_exceeds_capacity():
    solver = OrtoolsSolver()
    inp = _build_input(
        agent_ids=[1],
        qualified_postes_by_agent={1: (1,)},
        qualification_date_by_agent_poste={(1, 1): None},
        coverage_demands=[
            CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=2),
        ],
    )

    with pytest.raises(InfeasibleError):
        solver.generate(inp)


@pytest.mark.skip(reason="CP-SAT timeout status is not stable in CI with tiny limits")
def test_timeout_can_raise_timeout_error():
    solver = OrtoolsSolver()
    inp = _build_input(
        time_limit_seconds=0,
        agent_ids=list(range(1, 30)),
        qualified_postes_by_agent={a: (1,) for a in range(1, 30)},
        qualification_date_by_agent_poste={(a, 1): None for a in range(1, 30)},
        coverage_demands=[
            CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1),
            CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
        ],
    )

    with pytest.raises(TimeoutError):
        solver.generate(inp)


def test_no_demands_gives_zero_assignments_and_full_coverage():
    solver = OrtoolsSolver()
    out = solver.generate(_build_input())

    assert out.assignments == []
    assert out.stats["coverage_ratio"] == 1.0
    assert out.stats["num_variables"] == 0
    assert out.stats["objective_value"] == out.stats["score"]
    assert out.stats["num_constraints"] >= 0
    assert out.stats["demanded_pairs_count"] == 0


def test_copies_existing_day_type_when_unassigned():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            existing_day_type_by_agent_day={(1, date(2026, 1, 1)): "zcot"},
            coverage_demands=[],
        )
    )

    day = next(d for d in out.agent_days if d.agent_id == 1 and d.day_date == date(2026, 1, 1))
    assert day.day_type == "zcot"
