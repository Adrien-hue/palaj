from __future__ import annotations

from datetime import date, time
import time as time_module

import pytest
from ortools.sat.python import cp_model

from backend.app.services.solver.models import (
    CoverageDemand,
    InfeasibleError,
    SolverInput,
    TimeoutError,
    TrancheInfo,
)
from backend.app.services.solver.ortools_solver import MIN_LNS_REMAINING_SECONDS_TO_RUN_ITER, OrtoolsSolver


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


def test_feasible_status_with_time_limit_maps_to_timeout(monkeypatch):
    solver = OrtoolsSolver()
    _FakeCpSolver.status = cp_model.FEASIBLE
    _FakeCpSolver.wall_time = 0.1
    monkeypatch.setattr(cp_model, "CpSolver", _FakeCpSolver)

    out = solver.generate(_build_input(time_limit_seconds=60))

    assert out.stats["solver_status"] == "FEASIBLE"
    assert out.stats["solver_status_raw"] == "FEASIBLE"
    assert out.stats["normalized_solver_status"] == "TIMEOUT"
    assert out.stats["is_timeout"] is True
    assert out.stats["time_limit_reached"] is True


def test_feasible_status_without_time_limit_is_not_timeout(monkeypatch):
    solver = OrtoolsSolver()
    _FakeCpSolver.status = cp_model.FEASIBLE
    _FakeCpSolver.wall_time = 0.1
    monkeypatch.setattr(cp_model, "CpSolver", _FakeCpSolver)

    out = solver.generate(_build_input(time_limit_seconds=0))

    assert out.stats["solver_status"] == "FEASIBLE"
    assert out.stats["normalized_solver_status"] == "FEASIBLE"
    assert out.stats["is_timeout"] is False
    assert out.stats["time_limit_reached"] is False




def test_timeout_stats_debug_fields_present_in_failure_paths(monkeypatch):
    solver = OrtoolsSolver()
    _FakeCpSolver.status = cp_model.UNKNOWN
    _FakeCpSolver.wall_time = 0.1
    monkeypatch.setattr(cp_model, "CpSolver", _FakeCpSolver)

    with pytest.raises(InfeasibleError) as exc_info:
        solver.generate(_build_input(time_limit_seconds=60))

    stats = exc_info.value.stats
    assert stats["time_limit_seconds"] == 60.0
    assert stats["solver_max_time_seconds_applied"] == 60.0
    assert stats["solve_wall_time_seconds"] == pytest.approx(0.1)
    assert stats["solver_status_int"] == int(cp_model.UNKNOWN)
    assert stats["is_timeout"] == stats["time_limit_reached"]


def test_precheck_failure_keeps_timeout_debug_defaults():
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

    stats = exc_info.value.stats
    assert stats["time_limit_seconds"] == 5.0
    assert stats["solver_max_time_seconds_applied"] == 0.0
    assert stats["solve_wall_time_seconds"] == 0.0
    assert stats["solver_status_int"] is None
    assert stats["is_timeout"] is False
    assert stats["time_limit_reached"] is False


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


def test_soft_coverage_allows_solution_when_understaff_needed():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=2)],
        )
    )

    assert out.stats["solver_status"] in {"OPTIMAL", "FEASIBLE"}
    assert out.stats["understaff_total"] == 1
    assert out.stats["coverage_ratio"] < 1.0
    assert out.stats["num_assignments"] == 1


def test_weekday_weight_prioritizes_weekday_over_weekend():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 2),  # Friday
            end_date=date(2026, 1, 3),  # Saturday
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(17, 30), heure_fin=time(23, 0)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=11, required_count=1),
            ],
        )
    )

    covered = {(a.day_date, a.tranche_id) for a in out.assignments}
    # Business order: weekend day > weekday night.
    assert (date(2026, 1, 3), 11) in covered
    assert (date(2026, 1, 2), 10) not in covered
    assert out.stats["understaff_total"] == 1
    assert out.stats["understaff_total_weighted"] == OrtoolsSolver.W_UNDERSTAFF_WEEKDAY_NIGHT


def test_coverage_ratio_weighted_present_and_correct():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 2),  # Friday
            end_date=date(2026, 1, 3),  # Saturday
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(17, 30), heure_fin=time(23, 0)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=11, required_count=1),
            ],
        )
    )

    assert out.stats["coverage_ratio"] < 1.0
    assert out.stats["coverage_ratio_weighted"] > out.stats["coverage_ratio"]
    assert out.stats["total_required_weighted"] == 30


def test_useless_work_penalty_avoids_work_on_no_demand_days():
    solver = OrtoolsSolver()
    no_demand_day = date(2026, 1, 2)
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=no_demand_day,
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1)],
        )
    )

    assert out.stats["solver_status"] in {"OPTIMAL", "FEASIBLE"}
    assert out.stats["useless_work_total"] == 0
    assert all(a.day_date != no_demand_day for a in out.assignments)


def test_objective_prefers_lower_understaff_even_if_other_terms():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 2),
            end_date=date(2026, 1, 3),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(17, 30), heure_fin=time(23, 0)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=2),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=11, required_count=1),
            ],
        )
    )

    covered = {(a.day_date, a.tranche_id) for a in out.assignments}
    assert (date(2026, 1, 3), 11) in covered
    assert out.stats["understaff_total"] == 2
    assert out.stats["understaff_total_weighted"] == (
        2 * OrtoolsSolver.W_UNDERSTAFF_WEEKDAY_NIGHT
    )


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
    assert out.stats["coverage_ratio_weighted"] == 1.0


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


def test_rejects_invalid_combo_with_excessive_amplitude_soft_understaff():
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

    out = solver.generate(inp)

    assert out.stats["understaff_total"] == 1


def test_daily_rest_night_rule_blocks_incompatible_pair_with_soft_coverage():
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

    out = solver.generate(inp)

    assert out.stats["understaff_total"] == 1


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


def test_stats_combo_gating_counts_not_zero_with_soft_coverage():
    solver = OrtoolsSolver()
    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        agent_ids=[1],
        qualified_postes_by_agent={1: ()},
        qualification_date_by_agent_poste={},
        coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1)],
    )

    out = solver.generate(inp)

    assert out.stats["combo_candidate_pairs_count"] > 0
    assert out.stats["combo_allowed_pairs_count"] == 0
    assert out.stats["combo_rejected_not_qualified_count"] > 0
    assert out.stats["combo_rejected_samples"]
    assert any(sample["reason"] == "not_qualified" for sample in out.stats["combo_rejected_samples"])
    assert out.stats["understaff_total"] == 1


def test_stability_prefers_same_work_combo_on_consecutive_days():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
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
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
            ],
        )
    )

    assert out.stats["stability_changes_total"] >= 0
    assert out.stats["objective_terms"]["stability_changes"] == out.stats["stability_changes_total"]
    assert 1 in out.stats["stability_changes_by_agent"]


def test_work_block_starts_prefers_contiguous_work_when_coverage_equal():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(12, 0)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(13, 0), heure_fin=time(17, 0)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=10, required_count=1),
            ],
        )
    )

    assert out.stats["work_blocks_starts_total"] >= 1
    assert "work_blocks_starts_by_agent" in out.stats


def test_rpdouble_soft_stats_present():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            agent_ids=[1],
            qualified_postes_by_agent={1: ()},
            qualification_date_by_agent_poste={},
            coverage_demands=[],
        )
    )

    assert out.stats["rpdouble_soft_total"] >= 0
    assert out.stats["rpdouble_soft_by_agent"][1] >= 0


def test_tranche_diversity_bonus_prefers_using_multiple_main_tranches():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
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
    )

    assert out.stats["tranche_diversity_total"] >= 1
    assert out.stats["tranche_diversity_by_agent"][1] >= 1


def test_understaff_smoothing_stat_is_reported():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 2),
            end_date=date(2026, 1, 3),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(17, 30), heure_fin=time(23, 0)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=2),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=11, required_count=1),
            ],
        )
    )

    assert out.stats["understaff_smooth_weighted_sum"] >= out.stats["understaff_total"]
    assert out.stats["objective_terms"]["understaff_smooth_weighted"] == out.stats["understaff_smooth_weighted_sum"]


def test_coverage_priority_order_categories():
    solver = OrtoolsSolver()

    # weekday day > weekend day
    out_weekday_vs_weekend_day = solver.generate(
        _build_input(
            start_date=date(2026, 1, 2),  # Friday
            end_date=date(2026, 1, 3),  # Saturday
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=10, required_count=1),
            ],
        )
    )
    covered = {(a.day_date, a.tranche_id) for a in out_weekday_vs_weekend_day.assignments}
    assert (date(2026, 1, 2), 10) in covered

    # weekend day > weekday night
    out_weekend_day_vs_weekday_night = solver.generate(
        _build_input(
            start_date=date(2026, 1, 2),
            end_date=date(2026, 1, 3),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(17, 30), heure_fin=time(23, 0)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=11, required_count=1),
            ],
        )
    )
    covered2 = {(a.day_date, a.tranche_id) for a in out_weekend_day_vs_weekday_night.assignments}
    assert (date(2026, 1, 3), 11) in covered2
    assert (date(2026, 1, 2), 10) not in covered2

    # weekday night > weekend night
    out_weekday_night_vs_weekend_night = solver.generate(
        _build_input(
            start_date=date(2026, 1, 2),
            end_date=date(2026, 1, 3),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(17, 30), heure_fin=time(23, 0)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=10, required_count=1),
            ],
        )
    )
    covered3 = {(a.day_date, a.tranche_id) for a in out_weekday_night_vs_weekend_night.assignments}
    assert (date(2026, 1, 2), 10) in covered3


def test_smoothing_quadratic_spreads_understaff_when_required_gt_one():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            agent_ids=[1, 2],
            poste_ids=[1, 2],
            qualified_postes_by_agent={1: (1, 2), 2: (1, 2)},
            qualification_date_by_agent_poste={(1, 1): None, (1, 2): None, (2, 1): None, (2, 2): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
                TrancheInfo(id=11, poste_id=2, heure_debut=time(8, 0), heure_fin=time(13, 30)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=2),
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=11, required_count=2),
            ],
        )
    )

    covered_counts = {10: 0, 11: 0}
    for assignment in out.assignments:
        covered_counts[assignment.tranche_id] += 1
    # Total understaff is fixed at 2 (required 4, available 2), smoothing prefers split 1+1 over 2+0.
    assert out.stats["understaff_total"] == 2
    assert covered_counts[10] == 1
    assert covered_counts[11] == 1


def test_tranche_diversity_does_not_create_useless_work_or_coverage_loss():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(13, 30)),
                TrancheInfo(id=11, poste_id=1, heure_debut=time(17, 30), heure_fin=time(23, 0)),
            ],
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1)],
        )
    )

    assert out.stats["useless_work_total"] == 0
    assert all(a.tranche_id == 10 for a in out.assignments)
    assert out.stats["understaff_total"] == 0


def test_dominance_ratios_present_on_success_and_failure():
    solver = OrtoolsSolver()
    out = solver.generate(_build_input())
    ratios = out.stats["dominance_ratios"]
    assert ratios["cost_one_understaff_weekday_day"] > 0
    assert ratios["cost_one_understaff_weekend_day"] > 0
    assert ratios["cost_one_understaff_weekday_night"] > 0
    assert ratios["cost_one_understaff_weekend_night"] > 0
    assert "ratio_all_tiebreakers_vs_one_understaff_weekend_night" in ratios

    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=9999, required_count=1)],
    )
    with pytest.raises(InfeasibleError) as exc_info:
        solver.generate(inp)
    fail_ratios = exc_info.value.stats["dominance_ratios"]
    assert "cost_one_understaff_weekday_day" in fail_ratios
    assert "max_cost_all_tiebreakers" in fail_ratios

def test_v3_two_phase_non_regression_unweighted():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 4),
            time_limit_seconds=3,
            agent_ids=[1, 2],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=2),
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=2),
                CoverageDemand(day_date=date(2026, 1, 3), tranche_id=10, required_count=2),
                CoverageDemand(day_date=date(2026, 1, 4), tranche_id=10, required_count=2),
            ],
            v3_strategy="two_phase",
        )
    )
    p1 = out.stats.get("phase1_understaff_total_unweighted")
    p2 = out.stats.get("phase2_understaff_total_unweighted")
    if p1 is not None and p2 is not None:
        assert p2 <= p1


def test_v3_improves_raw_coverage_under_timeout_smoke():
    solver = OrtoolsSolver()
    baseline = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 5),
            time_limit_seconds=2,
            agent_ids=[1, 2],
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 6)],
            quality_profile="fast",
            v3_strategy="two_phase",
        )
    )
    balanced = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 5),
            time_limit_seconds=2,
            agent_ids=[1, 2],
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 6)],
            quality_profile="balanced",
            v3_strategy="two_phase_lns",
        )
    )
    assert balanced.stats["understaff_total"] <= baseline.stats["understaff_total"]


def test_v3_determinism_seed():
    solver = OrtoolsSolver()
    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 4),
        time_limit_seconds=2,
        coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=1) for d in range(1, 5)],
        seed=42,
        v3_strategy="two_phase",
    )
    out1 = solver.generate(inp)
    out2 = solver.generate(inp)
    assert out1.stats["understaff_total"] == out2.stats["understaff_total"]
    assert out1.stats["objective_value"] == out2.stats["objective_value"]
    sig1 = [(a.agent_id, a.day_date.isoformat(), a.tranche_id) for a in out1.assignments]
    sig2 = [(a.agent_id, a.day_date.isoformat(), a.tranche_id) for a in out2.assignments]
    assert sig1 == sig2


def test_v3_lns_poste_priority_deterministic():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            time_limit_seconds=2,
            agent_ids=[1, 2],
            qualified_postes_by_agent={1: (1, 2), 2: (1, 2)},
            qualification_date_by_agent_poste={(1, 1): None, (1, 2): None, (2, 1): None, (2, 2): None},
            poste_ids=[1, 2],
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(14, 0)),
                TrancheInfo(id=11, poste_id=2, heure_debut=time(8, 0), heure_fin=time(14, 0)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=2, poste_id=1),
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=11, required_count=1, poste_id=2),
            ],
            v3_strategy="two_phase_lns",
            lns_iter_seconds=0.5,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )
    assert out.stats["lns_iterations"] >= 1
    assert out.stats["lns_last_selected_poste_id"] == 1






def test_lns_pacing_stats_present():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            time_limit_seconds=4,
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=1, poste_id=1) for d in range(1, 4)],
            v3_strategy="two_phase_lns",
            lns_iter_seconds=0.5,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )

    stats = out.stats
    assert "lns_iterations_time_budget_max" in stats
    assert "lns_avg_solve_wall_time_seconds_iter" in stats
    assert "lns_min_solve_wall_time_seconds_iter" in stats
    assert "lns_max_solve_wall_time_seconds_iter" in stats
    assert "lns_solver_time_limit_seconds_applied" in stats
    assert stats["lns_iterations_time_budget_max"] >= 0
    assert stats["lns_min_solve_wall_time_seconds_iter"] <= stats["lns_avg_solve_wall_time_seconds_iter"] <= stats["lns_max_solve_wall_time_seconds_iter"]
    assert stats["lns_max_solve_wall_time_seconds_iter"] <= max(0.5, stats["lns_solver_time_limit_seconds_applied"]) + 0.25


def test_v3_lns_poste_plus_one_deterministic_selection_two_postes():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            time_limit_seconds=2,
            agent_ids=[1, 2],
            qualified_postes_by_agent={1: (1, 2), 2: (1, 2)},
            qualification_date_by_agent_poste={(1, 1): None, (1, 2): None, (2, 1): None, (2, 2): None},
            poste_ids=[1, 2],
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(14, 0)),
                TrancheInfo(id=11, poste_id=2, heure_debut=time(8, 0), heure_fin=time(14, 0)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=2, poste_id=1),
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=11, required_count=1, poste_id=2),
            ],
            v3_strategy="two_phase_lns",
            lns_neighborhood_mode="poste_plus_one",
            lns_iter_seconds=0.5,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )

    assert out.stats["lns_selected_postes_last"] == [1, 2]


def test_lns_iterations_do_not_spin_on_model_invalid(monkeypatch):
    solver = OrtoolsSolver()

    def _always_invalid(_self):
        return "forced invalid model for test"

    monkeypatch.setattr(cp_model.CpModel, "Validate", _always_invalid)

    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            time_limit_seconds=4,
            agent_ids=[1, 2],
            qualified_postes_by_agent={1: (1,), 2: (1,)},
            qualification_date_by_agent_poste={(1, 1): None, (2, 1): None},
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1, poste_id=1),
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1, poste_id=1),
            ],
            v3_strategy="two_phase_lns",
            lns_iter_seconds=2,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )

    assert out.stats["lns_model_invalid"] is True
    assert out.stats["lns_model_invalid_message"]
    assert out.stats["lns_iterations"] <= 1
    assert out.stats["lns_iterations_actual"] <= 1


def test_lns_iteration_history_status_strings_smoke():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            time_limit_seconds=4,
            agent_ids=[1, 2],
            qualified_postes_by_agent={1: (1,), 2: (1,)},
            qualification_date_by_agent_poste={(1, 1): None, (2, 1): None},
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=2, poste_id=1),
                CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=2, poste_id=1),
            ],
            v3_strategy="two_phase_lns",
            lns_iter_seconds=0.5,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )

    allowed = {"OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN", "MODEL_INVALID"}
    for entry in out.stats["lns_iteration_history"]:
        assert isinstance(entry["status_raw"], str)
        assert entry["status_raw"] in allowed
        assert "lns_iter_has_solution" in entry
        assert "lns_iter_status_raw" in entry
        assert "lns_iter_status_int" in entry
        assert "lns_iter_objective_value" in entry
        assert "lns_iter_understaff_total_unweighted" in entry
        assert "lns_iter_validate_message_present" in entry


def test_v3_lns_acceptance_strict_improve():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            time_limit_seconds=2,
            agent_ids=[1],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1, poste_id=1)],
            v3_strategy="two_phase_lns",
            lns_strict_improve=True,
            lns_iter_seconds=0.5,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )
    assert out.stats["lns_strict_improve"] is True
    assert out.stats["lns_accept_count"] == 0
    assert out.stats["lns_accept_count"] <= out.stats["lns_iterations"]


def test_v3_stats_present():
    solver = OrtoolsSolver()
    out = solver.generate(_build_input(v3_strategy="two_phase_lns", time_limit_seconds=2, coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1)]))
    for key in [
        "phase1_time_limit_seconds",
        "phase1_wall_time_seconds",
        "phase1_status_raw",
        "phase1_understaff_total_unweighted",
        "phase2_non_regression_constraint_applied",
        "lns_enabled",
        "lns_iterations",
        "lns_neighborhoods_tried_by_poste",
        "time_to_first_feasible_seconds",
        "best_objective_over_time_points",
        "top_understaff_days",
        "understaff_by_day_weighted",
        "smoothing_term_components_count",
        "model_build_wall_time_seconds",
        "phase2_model_rebuild_wall_time_seconds",
        "phase2_solve_wall_time_seconds",
        "phase2_reused_model",
        "lns_model_rebuild_wall_time_seconds_total",
        "lns_solve_wall_time_seconds_total",
        "lns_iteration_history",
        "lns_last_selected_poste_id",
        "lns_model_invalid",
        "lns_model_invalid_message",
        "lns_model_invalid_iteration_index",
        "lns_iterations_time_budget_max",
        "lns_avg_solve_wall_time_seconds_iter",
        "lns_min_solve_wall_time_seconds_iter",
        "lns_max_solve_wall_time_seconds_iter",
        "lns_solver_time_limit_seconds_applied",
        "lns_neighborhood_mode_used_counts",
        "lns_selected_postes_last",
        "lns_relaxed_days_count_last",
        "lns_fixed_days_count_last",
        "lns_fixed_y_count_last",
        "lns_relaxed_y_count_last",
        "lns_fixed_runs_count_last",
        "lns_relaxed_runs_count_last",
        "lns_iter_has_solution",
        "lns_iter_status_raw",
        "lns_iter_status_int",
        "lns_iter_objective_value",
        "lns_iter_understaff_total_unweighted",
        "lns_iter_validate_message_present",
        "lns_unknown_count_total",
        "lns_accept_count_total",
        "lns_no_solution_count_total",
        "lns_fallback_triggered",
        "lns_fallback_reason",
        "lns_neighborhood_mode_effective",
        "lns_poste_plus_one_top_days_k",
        "lns_poste_plus_one_top_days_selected_sample",
        "lns_poste_plus_one_top_days_days_sample",
        "lns_neighborhood_mode_requested",
        "lns_fallback_after_iterations",
        "lns_fallback_iteration_index",
        "lns_accept_count_at_fallback",
        "lns_last_accept_iteration_index",
        "lns_last_accept_t",
        "lns_early_stop_triggered",
        "lns_early_stop_reason",
        "lns_remaining_budget_seconds_at_stop",
        "lns_min_remaining_seconds_to_run_iter",
        "lns_history_truncated",
        "lns_history_max_items",
        "cp_sat_params_effective",
        "lns_iterations_actual",
        "decision_strategy_enabled",
        "decision_strategy_prioritized_vars_count",
        "decision_strategy_day_scores_top",
        "symmetry_breaking_enabled",
        "symmetry_constraints_count",
    ]:
        assert key in out.stats
    assert isinstance(out.stats["cp_sat_params_effective"], dict)
    assert "phase1" in out.stats["cp_sat_params_effective"]
    if out.stats["lns_iterations"] > 0:
        assert "lns" in out.stats["cp_sat_params_effective"]


def test_lns_top_days_global_produces_solutions():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 6),
            time_limit_seconds=5,
            seed=42,
            agent_ids=[1, 2],
            qualified_postes_by_agent={1: (1, 2), 2: (1, 2)},
            qualification_date_by_agent_poste={(1, 1): None, (1, 2): None, (2, 1): None, (2, 2): None},
            poste_ids=[1, 2],
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(14, 0)),
                TrancheInfo(id=11, poste_id=2, heure_debut=time(8, 0), heure_fin=time(14, 0)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2, poste_id=1)
                for d in range(1, 7)
            ]
            + [CoverageDemand(day_date=date(2026, 1, d), tranche_id=11, required_count=1, poste_id=2) for d in range(1, 7)],
            v3_strategy="two_phase_lns",
            lns_neighborhood_mode="top_days_global",
            lns_iter_seconds=0.3,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )

    stats = out.stats
    assert stats["lns_iterations"] > 0
    assert stats["lns_unknown_count_total"] < stats["lns_iterations"]
    assert any(entry.get("lns_iter_has_solution") for entry in stats["lns_iteration_history"])
    assert stats["lns_best_objective_value"] is not None


def test_lns_fallback_triggers_on_no_solution_or_no_acceptance(monkeypatch):
    solver = OrtoolsSolver()
    original_solve = cp_model.CpSolver.Solve
    call_counter = {"count": 0}

    def _solve_with_unknown_in_lns(self, model, *args, **kwargs):
        call_counter["count"] += 1
        if call_counter["count"] >= 3:
            return cp_model.UNKNOWN
        return original_solve(self, model, *args, **kwargs)

    monkeypatch.setattr(cp_model.CpSolver, "Solve", _solve_with_unknown_in_lns)

    with pytest.raises(InfeasibleError) as exc_info:
        solver.generate(
            _build_input(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 8),
                time_limit_seconds=8,
                coverage_demands=[
                    CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2, poste_id=1)
                    for d in range(1, 9)
                ],
                v3_strategy="two_phase_lns",
                lns_neighborhood_mode="top_days_global",
                lns_iter_seconds=0.05,
                lns_min_remaining_seconds=0,
                min_lns_seconds=0,
            )
        )

    stats = exc_info.value.stats
    assert stats["lns_fallback_triggered"] is True
    assert stats["lns_neighborhood_mode_effective"] == "poste_plus_one"
    assert stats["lns_fallback_reason"] in {"too_many_unknown", "no_acceptance_in_requested_mode"}
    assert isinstance(stats["lns_fallback_after_iterations"], int)


def test_lns_fallback_no_acceptance_reason_and_context_stats():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 12),
            time_limit_seconds=8,
            seed=101,
            agent_ids=[1, 2],
            qualified_postes_by_agent={1: (1, 2), 2: (1, 2)},
            qualification_date_by_agent_poste={(1, 1): None, (1, 2): None, (2, 1): None, (2, 2): None},
            poste_ids=[1, 2],
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(14, 0)),
                TrancheInfo(id=11, poste_id=2, heure_debut=time(8, 0), heure_fin=time(14, 0)),
            ],
            coverage_demands=[
                CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2, poste_id=1)
                for d in range(1, 13)
            ]
            + [CoverageDemand(day_date=date(2026, 1, d), tranche_id=11, required_count=1, poste_id=2) for d in range(1, 13)],
            v3_strategy="two_phase_lns",
            lns_neighborhood_mode="top_days_global",
            lns_iter_seconds=0.2,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )

    stats = out.stats
    assert stats["lns_fallback_triggered"] is True
    assert stats["lns_fallback_reason"] != "no_acceptance"
    assert stats["lns_fallback_reason"] in {"no_acceptance_over_last_k_iters", "no_acceptance_in_requested_mode", "too_many_unknown"}
    assert stats["lns_fallback_iteration_index"] is not None
    assert isinstance(stats["lns_accept_count_at_fallback"], int)
    assert stats["lns_accept_count_at_fallback"] >= 0
    assert (stats["lns_last_accept_iteration_index"] is None) or isinstance(stats["lns_last_accept_iteration_index"], int)
    if stats["lns_fallback_reason"] in {"no_acceptance_over_last_k_iters", "no_acceptance_in_requested_mode"}:
        assert stats["lns_fallback_reason"] == "no_acceptance_in_requested_mode"
    if stats["lns_last_accept_iteration_index"] is not None:
        assert stats["lns_last_accept_iteration_index"] < stats["lns_fallback_iteration_index"]


def test_lns_early_stop_when_remaining_budget_too_small(monkeypatch):
    solver = OrtoolsSolver()
    ticks = iter([
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.21,
    ])

    def _fake_monotonic():
        return next(ticks, 0.21)

    monkeypatch.setattr(time_module, "monotonic", _fake_monotonic)

    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 4),
            time_limit_seconds=0.25,
            seed=7,
            agent_ids=[1, 2],
            qualified_postes_by_agent={1: (1,), 2: (1,)},
            qualification_date_by_agent_poste={(1, 1): None, (2, 1): None},
            poste_ids=[1],
            tranches=[TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(14, 0))],
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=1, poste_id=1) for d in range(1, 5)],
            v3_strategy="two_phase_lns",
            lns_neighborhood_mode="poste_only",
            lns_iter_seconds=0.1,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )

    stats = out.stats
    assert stats["lns_early_stop_triggered"] is True
    assert stats["lns_early_stop_reason"] == "remaining_budget_too_small"
    assert stats["lns_remaining_budget_seconds_at_stop"] is not None
    assert stats["lns_remaining_budget_seconds_at_stop"] < stats["lns_min_remaining_seconds_to_run_iter"]
    assert stats["lns_min_remaining_seconds_to_run_iter"] == MIN_LNS_REMAINING_SECONDS_TO_RUN_ITER
    assert stats["lns_iterations_actual"] <= 1
    if stats["lns_iteration_history"]:
        assert stats["lns_iteration_history"][-1]["status_raw"] != "UNKNOWN"


def test_lns_new_stats_defaults_present_without_triggers():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            time_limit_seconds=5,
            seed=11,
            v3_strategy="two_phase_lns",
            lns_neighborhood_mode="poste_only",
            lns_iter_seconds=0.3,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=1, poste_id=1) for d in range(1, 4)],
        )
    )

    stats = out.stats
    for key in [
        "lns_fallback_iteration_index",
        "lns_accept_count_at_fallback",
        "lns_last_accept_iteration_index",
        "lns_last_accept_t",
        "lns_early_stop_triggered",
        "lns_early_stop_reason",
        "lns_remaining_budget_seconds_at_stop",
        "lns_min_remaining_seconds_to_run_iter",
    ]:
        assert key in stats
    assert stats["lns_fallback_iteration_index"] is None
    assert stats["lns_accept_count_at_fallback"] == stats["lns_accept_count_total"]
    assert stats["lns_accept_count_total"] == stats["lns_accept_count"]
    assert isinstance(stats["lns_early_stop_triggered"], bool)
    if stats["lns_early_stop_triggered"]:
        assert stats["lns_early_stop_reason"] == "remaining_budget_too_small"
        assert stats["lns_remaining_budget_seconds_at_stop"] is not None
    else:
        assert stats["lns_early_stop_reason"] is None
        assert stats["lns_remaining_budget_seconds_at_stop"] is None



def test_poste_plus_one_top_days_selects_expected_days():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 5),
            time_limit_seconds=5,
            seed=99,
            agent_ids=[1, 2],
            qualified_postes_by_agent={1: (1, 2), 2: (1, 2)},
            qualification_date_by_agent_poste={(1, 1): None, (1, 2): None, (2, 1): None, (2, 2): None},
            poste_ids=[1, 2],
            tranches=[
                TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(14, 0)),
                TrancheInfo(id=11, poste_id=2, heure_debut=time(8, 0), heure_fin=time(14, 0)),
            ],
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2, poste_id=1) for d in range(1, 6)],
            v3_strategy="two_phase_lns",
            lns_neighborhood_mode="poste_plus_one_top_days",
            lns_max_days_to_relax=2,
            lns_iter_seconds=0.3,
            lns_min_remaining_seconds=0,
            min_lns_seconds=0,
        )
    )

    weighted = out.stats["understaff_by_day_weighted"]
    expected_days = [day for day, _value in sorted(weighted.items(), key=lambda item: (-item[1], item[0]))[:2]]
    assert out.stats["lns_poste_plus_one_top_days_k"] == 2
    assert out.stats["lns_poste_plus_one_top_days_selected_sample"][:2] == expected_days
    assert out.stats["lns_poste_plus_one_top_days_days_sample"][:2] == expected_days


def test_v3_decision_strategy_stats_present():
    solver = OrtoolsSolver()
    out = solver.generate(
        _build_input(
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1)],
            enable_decision_strategy=True,
            v3_strategy="two_phase",
        )
    )
    assert "decision_strategy_enabled" in out.stats
    assert "decision_strategy_prioritized_vars_count" in out.stats
    assert "decision_strategy_day_scores_top" in out.stats


def test_v3_symmetry_breaking_determinism_smoke():
    solver = OrtoolsSolver()
    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 3),
        coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=1) for d in range(1, 4)],
        enable_symmetry_breaking=True,
        seed=7,
        v3_strategy="two_phase",
    )
    out1 = solver.generate(inp)
    out2 = solver.generate(inp)
    assert out1.stats["understaff_total"] == out2.stats["understaff_total"]
    assert out1.stats["objective_value"] == out2.stats["objective_value"]


def test_v32_smoke_not_worse_than_v31_profile():
    solver = OrtoolsSolver()
    base = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 3)],
            time_limit_seconds=1,
            enable_decision_strategy=False,
            enable_symmetry_breaking=False,
            v3_strategy="two_phase",
        )
    )
    guided = solver.generate(
        _build_input(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 3)],
            time_limit_seconds=1,
            enable_decision_strategy=True,
            enable_symmetry_breaking=True,
            v3_strategy="two_phase",
        )
    )
    assert guided.stats["understaff_total"] <= base.stats["understaff_total"]
