from __future__ import annotations

from datetime import date, time

import pytest
from ortools.sat.python import cp_model

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
        tranches=[TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(14, 0))],
        coverage_demands=[],
    )
    base.update(kwargs)
    return SolverInput(**base)


class _FakeCpSolver:
    status = None
    wall_time = 0.0

    def __init__(self):
        self.parameters = type("P", (), {"max_time_in_seconds": None, "num_search_workers": None, "random_seed": None})()

    def Solve(self, _model):
        return self.status

    def WallTime(self):
        return self.wall_time

    def Value(self, _var):
        return 0


def test_unknown_near_time_limit_maps_to_timeout(monkeypatch):
    solver = OrtoolsSolver()
    _FakeCpSolver.status = cp_model.UNKNOWN
    _FakeCpSolver.wall_time = 5.0
    monkeypatch.setattr(cp_model, "CpSolver", _FakeCpSolver)

    with pytest.raises(TimeoutError) as exc_info:
        solver.generate(_build_input(time_limit_seconds=5))

    assert exc_info.value.stats["solver_status"] == "UNKNOWN"
    assert exc_info.value.stats["solver_status_raw"] == "UNKNOWN"
    assert exc_info.value.stats["normalized_solver_status"] == "TIMEOUT"
    assert exc_info.value.stats["is_timeout"] is True


def test_unknown_far_from_time_limit_maps_to_infeasible(monkeypatch):
    solver = OrtoolsSolver()
    _FakeCpSolver.status = cp_model.UNKNOWN
    _FakeCpSolver.wall_time = 0.1
    monkeypatch.setattr(cp_model, "CpSolver", _FakeCpSolver)

    with pytest.raises(InfeasibleError) as exc_info:
        solver.generate(_build_input(time_limit_seconds=60))

    assert exc_info.value.stats["solver_status"] == "UNKNOWN"
    assert exc_info.value.stats["normalized_solver_status"] == "UNKNOWN"
    assert exc_info.value.stats["is_timeout"] is False
    assert exc_info.value.stats["timeout_confidence"] == "low"


def test_feasible_status_is_not_timeout_with_mocked_solver(monkeypatch):
    solver = OrtoolsSolver()
    _FakeCpSolver.status = cp_model.FEASIBLE
    _FakeCpSolver.wall_time = 0.1
    monkeypatch.setattr(cp_model, "CpSolver", _FakeCpSolver)

    out = solver.generate(_build_input(time_limit_seconds=60))

    assert out.stats["solver_status"] == "FEASIBLE"
    assert out.stats["normalized_solver_status"] == "FEASIBLE"
    assert out.stats["is_timeout"] is False


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
    assert out.stats["coverage_constraints_count"] == 2
    assert out.stats["num_combos_used_in_solution"] >= 1
    assert out.stats["num_combos_in_model"] >= out.stats["num_combos_used_in_solution"]


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

    with pytest.raises(InfeasibleError) as exc_info:
        solver.generate(inp)

    assert exc_info.value.stats["solver_status"] == "INFEASIBLE"
    assert exc_info.value.stats["num_variables"] > 0
    assert exc_info.value.stats["demand_count"] == 1
    assert exc_info.value.stats["total_required_work_minutes"] == 720
    assert exc_info.value.stats["variable_count_method"] == "internal_counter"
    assert exc_info.value.stats["constraint_count_method"] == "internal_counter"
    assert "required_minutes_estimate_method" in exc_info.value.stats
    assert exc_info.value.stats["combo_allowed_pairs_count"] > 0
    assert exc_info.value.stats["y_variables_count"] > 0
    assert exc_info.value.stats["num_combos_in_model"] > 0
    assert exc_info.value.stats["num_combos_used_in_solution"] is None
    assert exc_info.value.stats["num_combos_effective"] == exc_info.value.stats["num_combos_in_model"]


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
    assert out.stats["num_variables"] > 0
    assert out.stats["objective_value"] == out.stats["score"]
    assert out.stats["num_constraints"] >= 0
    assert out.stats["demanded_pairs_count"] == 0
    assert out.stats["coverage_constraints_count"] == 0


def test_copies_existing_day_type_when_unassigned():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            agent_ids=[1],
            qualified_postes_by_agent={1: ()},
            qualification_date_by_agent_poste={},
            existing_day_type_by_agent_day={(1, date(2026, 1, 1)): "zcot"},
            coverage_demands=[],
        )
    )

    day = next(d for d in out.agent_days if d.agent_id == 1 and d.day_date == date(2026, 1, 1))
    assert day.day_type == "zcot"


def test_allows_multi_tranche_same_day_when_combo_valid():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(11, 0)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(11, 0), heure_fin=time(14, 0)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1),
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=11, required_count=1),
            ],
        )
    )

    assert {(a.agent_id, a.tranche_id) for a in out.assignments} == {(1, 10), (1, 11)}


def test_rejects_invalid_combo_with_excessive_amplitude():
    solver = OrtoolsSolver()
    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        agent_ids=[1],
        qualified_postes_by_agent={1: (1,)},
        qualification_date_by_agent_poste={(1, 1): None},
        tranches=[
            TrancheInfo(id=10, poste_id=1, heure_debut=time(6, 0), heure_fin=time(11, 30)),
            TrancheInfo(id=11, poste_id=1, heure_debut=time(18, 0), heure_fin=time(23, 30)),
        ],
        coverage_demands=[
            CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1),
            CoverageDemand(day_date=date(2026, 1, 1), tranche_id=11, required_count=1),
        ],
    )

    with pytest.raises(InfeasibleError):
        solver.generate(inp)


def test_daily_rest_night_rule_blocks_incompatible_pair():
    solver = OrtoolsSolver()
    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 2),
        agent_ids=[1],
        qualified_postes_by_agent={1: (1,)},
        qualification_date_by_agent_poste={(1, 1): None},
        tranches=[
            TrancheInfo(id=10, poste_id=1, heure_debut=time(17, 30), heure_fin=time(23, 0)),
            TrancheInfo(id=11, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
        ],
        coverage_demands=[
            CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1),
            CoverageDemand(day_date=date(2026, 1, 2), tranche_id=11, required_count=1),
        ],
    )

    with pytest.raises(InfeasibleError):
        solver.generate(inp)


def test_no_implicit_zero_demand_constraints_are_added():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(13, 30), heure_fin=time(19, 0)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1),
            ],
        )
    )

    assert out.stats["coverage_constraints_count"] == 1
    assert any(a.tranche_id == 10 for a in out.assignments)


def test_stats_missing_tranche_in_any_combo_precheck():
    solver = OrtoolsSolver()
    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        agent_ids=[1],
        qualified_postes_by_agent={1: (1,)},
        qualification_date_by_agent_poste={(1, 1): None},
        coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=9999, required_count=1)],
    )

    with pytest.raises(InfeasibleError) as exc_info:
        solver.generate(inp)

    assert exc_info.value.stats["missing_tranche_in_any_combo_count"] == 1
    assert 9999 in exc_info.value.stats["missing_tranche_in_any_combo_sample"]
    assert exc_info.value.stats["solver_status_raw"] == "PRECHECK_INFEASIBLE"


def test_stats_combo_gating_counts_not_zero():
    solver = OrtoolsSolver()
    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        agent_ids=[1],
        qualified_postes_by_agent={1: ()},
        qualification_date_by_agent_poste={},
        coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1)],
    )

    with pytest.raises(InfeasibleError) as exc_info:
        solver.generate(inp)

    assert exc_info.value.stats["combo_candidate_pairs_count"] > 0
    assert exc_info.value.stats["combo_allowed_pairs_count"] == 0
    assert exc_info.value.stats["combo_rejected_not_qualified_count"] > 0
    assert exc_info.value.stats["combo_rejected_samples"]
    assert any(sample["reason"] == "not_qualified" for sample in exc_info.value.stats["combo_rejected_samples"])
