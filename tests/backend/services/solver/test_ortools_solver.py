from __future__ import annotations

from datetime import date, time

import pytest

from backend.app.services.solver.constants import SOLVER_VERSION, STATS_PAYLOAD_CAPS
from backend.app.services.solver.constants import RESULT_STATS_SCHEMA_VERSION
from backend.app.services.solver.stats import StatsCollector
from backend.app.services.solver.models import CoverageDemand, SolverInput, TrancheInfo
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


def _grouped(out: object) -> dict:
    return out.stats["stats"]


def test_no_legacy_result_stats_root_keys():
    out = OrtoolsSolver().generate(_build_input())
    assert set(out.stats.keys()) == {"result_stats_schema_version", "stats"}
    assert out.stats["result_stats_schema_version"] == 3


def test_grouped_family_presence_and_minimal_required_keys():
    grouped = _grouped(OrtoolsSolver().generate(_build_input()))

    for family in ["meta", "timing", "model", "coverage", "objective", "solution_quality", "lns", "cp_sat"]:
        assert family in grouped

    assert grouped["meta"]["schema_version"] == 3
    assert grouped["meta"]["solver_version"] == SOLVER_VERSION == "v3"
    assert grouped["meta"]["verbosity"] in {"debug", "compact"}

    for key in ["time_limit_seconds", "solve_wall_time_seconds", "model_build_wall_time_seconds"]:
        assert key in grouped["timing"]["global"]

    for key in ["agent_count", "poste_count", "demand_count", "num_variables", "num_constraints"]:
        assert key in grouped["model"]

    for key in ["coverage_ratio", "understaff_total", "top_understaff_days", "understaff_by_day_weighted"]:
        assert key in grouped["coverage"]

    for key in ["objective_value", "score", "objective_terms", "dominance_ratios"]:
        assert key in grouped["objective"]

    for key in ["soft_violations", "nights_total", "workload_avg", "num_assignments"]:
        assert key in grouped["solution_quality"]

    for key in ["lns_iterations", "lns_iterations_actual", "iteration_history", "lns_enabled"]:
        assert key in grouped["lns"]

    for key in ["cp_sat_params_effective", "phases", "best_objective_over_time_points"]:
        assert key in grouped["cp_sat"]


def test_schema_version_consistency_between_root_and_meta():
    out = OrtoolsSolver().generate(_build_input())
    assert out.stats["result_stats_schema_version"] == out.stats["stats"]["meta"]["schema_version"]
    assert out.stats["stats"]["meta"]["schema_version"] == RESULT_STATS_SCHEMA_VERSION


def test_deterministic_sentinel_values_stable_across_runs():
    solver = OrtoolsSolver()
    inp = _build_input(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 4),
        seed=42,
        time_limit_seconds=3,
        coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2, poste_id=1) for d in range(1, 5)],
        v3_strategy="two_phase_lns",
        lns_iter_seconds=0.4,
        lns_min_remaining_seconds=0,
        min_lns_seconds=0,
    )

    run1 = _grouped(solver.generate(inp))
    run2 = _grouped(solver.generate(inp))

    fields = [
        ("model", "agent_count"),
        ("model", "poste_count"),
        ("model", "tranche_count"),
        ("model", "demand_count"),
        ("model", "num_variables"),
        ("model", "num_constraints"),
        ("coverage", "coverage_ratio"),
        ("coverage", "understaff_total"),
        ("coverage", "coverage_ratio_weighted"),
        ("model", "coverage_constraints_count"),
    ]
    for family, key in fields:
        assert run1[family][key] == run2[family][key]


def test_cross_family_coherence_invariants():
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 5),
                seed=42,
                time_limit_seconds=3,
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2, poste_id=1) for d in range(1, 6)],
                v3_strategy="two_phase_lns",
                lns_iter_seconds=0.4,
                lns_min_remaining_seconds=0,
                min_lns_seconds=0,
            )
        )
    )

    objective = grouped["objective"]
    cp_sat = grouped["cp_sat"]

    assert objective["score"] == objective["objective_value"]

    points = cp_sat["best_objective_over_time_points"]
    assert isinstance(points, list)
    prev_t = -1.0
    for point in points:
        assert point["t"] >= 0
        assert point["t"] >= prev_t
        prev_t = point["t"]

    ttff = cp_sat.get("time_to_first_feasible_seconds")
    if ttff is not None:
        assert ttff >= 0
        if points:
            assert abs(points[0]["t"] - ttff) <= 0.05


def test_lns_iteration_history_single_canonical_list_and_item_shape():
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 5),
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 6)],
                v3_strategy="two_phase_lns",
                lns_iter_seconds=0.3,
                lns_min_remaining_seconds=0,
                min_lns_seconds=0,
            )
        )
    )

    lns = grouped["lns"]
    assert "lns_iteration_history" not in lns
    assert isinstance(lns["iteration_history"], list)

    expected_keys = {
        "t",
        "poste_id",
        "selected_postes",
        "relaxed_days_count",
        "fixed_y_count",
        "relaxed_y_count",
        "neighborhood_mode_effective",
        "status_raw",
        "status_int",
        "validate_message_present",
        "accepted",
        "solve_wall_time_seconds_iter",
        "understaff_total_unweighted",
        "objective_value",
    }
    for item in lns["iteration_history"]:
        assert set(item.keys()) == expected_keys


def test_lns_invariants_effective_last_and_budget_ordering():
    lns = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 6),
                time_limit_seconds=1,
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 7)],
                v3_strategy="two_phase_lns",
                lns_iter_seconds=0.6,
                lns_min_remaining_seconds=0.3,
                min_lns_seconds=0,
            )
        )
    )["lns"]

    if lns.get("lns_early_stop_reason") == "remaining_budget_too_small_for_iter":
        assert lns.get("lns_iter_time_limit_seconds_effective_last") is None

    intended = lns.get("lns_intended_iter_time_limit_seconds_last")
    effective = lns.get("lns_iter_time_limit_seconds_effective_last")
    if intended is not None and effective is not None:
        assert effective <= intended


def test_debug_mode_heavy_field_metadata_and_type_stability(monkeypatch):
    monkeypatch.setenv("PLANNING_STATS_VERBOSITY", "debug")
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 20),
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 21)],
                v3_strategy="two_phase_lns",
                lns_neighborhood_mode="top_days_global",
                lns_iter_seconds=0.3,
                lns_min_remaining_seconds=0,
                min_lns_seconds=0,
            )
        )
    )

    model = grouped["model"]
    lns = grouped["lns"]
    coverage = grouped["coverage"]

    assert isinstance(model["combo_rejected_samples"], list)
    assert model["combo_rejected_samples_total"] >= len(model["combo_rejected_samples"])
    assert len(model["combo_rejected_samples"]) <= STATS_PAYLOAD_CAPS["debug"]["combo_rejected_samples"]
    assert isinstance(model["combo_rejected_samples_truncated"], bool)
    assert model["combo_allowed_samples_total"] >= len(model["combo_allowed_samples"])
    assert len(model["combo_allowed_samples"]) <= STATS_PAYLOAD_CAPS["debug"]["combo_allowed_samples"]
    assert isinstance(model["combo_allowed_samples_truncated"], bool)
    assert model["missing_tranche_in_any_combo_sample_total"] >= len(model["missing_tranche_in_any_combo_sample"])
    assert len(model["missing_tranche_in_any_combo_sample"]) <= STATS_PAYLOAD_CAPS["debug"]["missing_tranche_in_any_combo_sample"]
    assert isinstance(model["missing_tranche_in_any_combo_sample_truncated"], bool)

    assert isinstance(lns["iteration_history"], list)
    assert lns["iteration_history_total"] >= len(lns["iteration_history"])
    assert len(lns["iteration_history"]) <= STATS_PAYLOAD_CAPS["debug"]["lns_iteration_history"]
    assert isinstance(lns["iteration_history_truncated"], bool)

    assert isinstance(coverage["top_understaff_days"], list)
    assert coverage["top_understaff_days_total"] >= len(coverage["top_understaff_days"])
    assert len(coverage["top_understaff_days"]) <= STATS_PAYLOAD_CAPS["debug"]["top_understaff_days"]
    assert isinstance(coverage["top_understaff_days_truncated"], bool)
    assert isinstance(coverage["understaff_by_day_weighted"], dict)
    assert coverage["understaff_by_day_weighted_total"] >= len(coverage["understaff_by_day_weighted"])
    assert isinstance(coverage["understaff_by_day_weighted_truncated"], bool)

    cp_sat = grouped["cp_sat"]
    assert isinstance(cp_sat["best_objective_over_time_points"], list)
    assert cp_sat["best_objective_over_time_points_total"] >= len(cp_sat["best_objective_over_time_points"])
    assert len(cp_sat["best_objective_over_time_points"]) <= STATS_PAYLOAD_CAPS["debug"]["cp_sat_best_objective_points"]
    assert isinstance(cp_sat["best_objective_over_time_points_truncated"], bool)


def test_compact_mode_truncation_metadata_and_type_stability(monkeypatch):
    monkeypatch.setenv("PLANNING_STATS_VERBOSITY", "compact")
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 20),
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 21)],
                v3_strategy="two_phase_lns",
                lns_neighborhood_mode="top_days_global",
                lns_iter_seconds=0.3,
                lns_min_remaining_seconds=0,
                min_lns_seconds=0,
            )
        )
    )

    assert grouped["meta"]["verbosity"] == "compact"
    model = grouped["model"]
    lns = grouped["lns"]
    coverage = grouped["coverage"]

    assert isinstance(lns["iteration_history"], list)
    assert isinstance(lns["iteration_history_total"], int)
    assert lns["iteration_history_total"] >= len(lns["iteration_history"])
    assert isinstance(lns["iteration_history_truncated"], bool)

    for field in ["combo_rejected_samples", "combo_allowed_samples", "missing_tranche_in_any_combo_sample"]:
        assert isinstance(model[field], list)
        assert isinstance(model[f"{field}_total"], int)
        assert model[f"{field}_total"] >= len(model[field])
        assert isinstance(model[f"{field}_truncated"], bool)

    assert isinstance(coverage["top_understaff_days"], list)
    assert isinstance(coverage["top_understaff_days_total"], int)
    assert coverage["top_understaff_days_total"] >= len(coverage["top_understaff_days"])
    assert isinstance(coverage["top_understaff_days_truncated"], bool)

    assert isinstance(coverage["understaff_by_day_weighted"], dict)
    assert all(v > 0 for v in coverage["understaff_by_day_weighted"].values())
    assert isinstance(coverage["understaff_by_day_weighted_total"], int)
    assert coverage["understaff_by_day_weighted_total"] >= len(coverage["understaff_by_day_weighted"])
    assert isinstance(coverage["understaff_by_day_weighted_truncated"], bool)

    cp_sat = grouped["cp_sat"]
    assert isinstance(cp_sat["best_objective_over_time_points"], list)
    assert isinstance(cp_sat["best_objective_over_time_points_total"], int)
    assert cp_sat["best_objective_over_time_points_total"] >= len(cp_sat["best_objective_over_time_points"])
    assert len(cp_sat["best_objective_over_time_points"]) <= STATS_PAYLOAD_CAPS["compact"]["cp_sat_best_objective_points"]
    assert isinstance(cp_sat["best_objective_over_time_points_truncated"], bool)


def test_stats_collector_is_single_trimming_source_for_heavy_fields_debug():
    collector = StatsCollector(verbosity="debug")
    flat = {
        "lns_iteration_history": [
            {
                "t": i,
                "poste_id": 1,
                "selected_postes": [1],
                "relaxed_days_count": 1,
                "fixed_y_count": 1,
                "relaxed_y_count": 1,
                "neighborhood_mode_effective": "poste_only",
                "solve_wall_time_seconds_iter": 0.1,
                "accepted": False,
                "status_raw": "FEASIBLE",
                "status_int": 2,
                "validate_message_present": False,
                "understaff_total_unweighted": 1,
                "objective_value": 10,
                "legacy": "drop",
            }
            for i in range(130)
        ],
        "best_objective_over_time_points": [{"t": i / 10, "obj": 100 - i, "understaff_unweighted": i} for i in range(260)],
        "combo_rejected_samples": [{"id": i} for i in range(75)],
        "combo_allowed_samples": [{"id": i} for i in range(75)],
        "missing_tranche_in_any_combo_sample": list(range(75)),
        "top_understaff_days": [{"day_date": f"2026-01-{i:02d}"} for i in range(35)],
        "understaff_by_day_weighted": {
            "2026-01-01": 3,
            "2026-01-03": 2,
            "2026-01-05": 1,
        },
    }
    grouped = collector.finalize(flat)["stats"]

    assert grouped["lns"]["iteration_history_total"] == 130
    assert len(grouped["lns"]["iteration_history"]) == STATS_PAYLOAD_CAPS["debug"]["lns_iteration_history"]
    assert grouped["lns"]["iteration_history_truncated"] is True
    assert all("legacy" not in item for item in grouped["lns"]["iteration_history"])

    assert grouped["cp_sat"]["best_objective_over_time_points_total"] == 260
    assert len(grouped["cp_sat"]["best_objective_over_time_points"]) == STATS_PAYLOAD_CAPS["debug"]["cp_sat_best_objective_points"]
    assert grouped["cp_sat"]["best_objective_over_time_points_truncated"] is True

    assert grouped["model"]["combo_rejected_samples_total"] == 75
    assert len(grouped["model"]["combo_rejected_samples"]) == STATS_PAYLOAD_CAPS["debug"]["combo_rejected_samples"]
    assert grouped["model"]["combo_rejected_samples_truncated"] is True

    assert grouped["coverage"]["top_understaff_days_total"] == 35
    assert len(grouped["coverage"]["top_understaff_days"]) == STATS_PAYLOAD_CAPS["debug"]["top_understaff_days"]
    assert grouped["coverage"]["top_understaff_days_truncated"] is True
    assert grouped["coverage"]["understaff_by_day_weighted_total"] == 5
    assert grouped["coverage"]["understaff_by_day_weighted_truncated"] is False
    assert len(grouped["coverage"]["understaff_by_day_weighted"]) == 5
    assert grouped["coverage"]["understaff_by_day_weighted"]["2026-01-02"] == 0
    assert any(v == 0 for v in grouped["coverage"]["understaff_by_day_weighted"].values())


def test_heavy_fields_metadata_consistency_when_not_truncated():
    collector = StatsCollector(verbosity="debug")
    flat = {
        "lns_iteration_history": [
            {
                "t": 1,
                "poste_id": 1,
                "selected_postes": [1],
                "relaxed_days_count": 1,
                "fixed_y_count": 1,
                "relaxed_y_count": 0,
                "neighborhood_mode_effective": "poste_only",
                "solve_wall_time_seconds_iter": 0.1,
                "accepted": True,
                "status_raw": "FEASIBLE",
                "status_int": 2,
                "validate_message_present": False,
                "understaff_total_unweighted": 0,
                "objective_value": 1,
            }
        ],
        "best_objective_over_time_points": [{"t": 0.1, "obj": 1, "understaff_unweighted": 0}],
        "combo_rejected_samples": [{"id": 1}],
        "combo_allowed_samples": [{"id": 2}],
        "missing_tranche_in_any_combo_sample": [10],
        "top_understaff_days": [{"day_date": "2026-01-01", "understaff_unweighted": 0, "understaff_weighted": 0}],
        "understaff_by_day_weighted": {"2026-01-01": 0},
    }

    grouped = collector.finalize(flat)["stats"]
    checks = [
        (grouped["lns"], "iteration_history"),
        (grouped["cp_sat"], "best_objective_over_time_points"),
        (grouped["model"], "combo_rejected_samples"),
        (grouped["model"], "combo_allowed_samples"),
        (grouped["model"], "missing_tranche_in_any_combo_sample"),
        (grouped["coverage"], "top_understaff_days"),
    ]

    for container, field in checks:
        assert container[f"{field}_total"] >= len(container[field])
        if container[f"{field}_total"] == len(container[field]):
            assert container[f"{field}_truncated"] is False

    coverage = grouped["coverage"]
    assert coverage["understaff_by_day_weighted_total"] >= len(coverage["understaff_by_day_weighted"])
    if coverage["understaff_by_day_weighted_total"] == len(coverage["understaff_by_day_weighted"]):
        assert coverage["understaff_by_day_weighted_truncated"] is False


def test_lns_iteration_history_has_no_legacy_prefixed_keys():
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 5),
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2) for d in range(1, 6)],
                v3_strategy="two_phase_lns",
                lns_iter_seconds=0.3,
                lns_min_remaining_seconds=0,
                min_lns_seconds=0,
            )
        )
    )

    for item in grouped["lns"]["iteration_history"]:
        for key in item.keys():
            assert not key.startswith("lns_iter_")
            assert not key.startswith("lns_")


def test_cp_sat_duplication_rules_and_canonical_locations():
    grouped = _grouped(
        OrtoolsSolver().generate(_build_input(v3_strategy="two_phase_lns", lns_iter_seconds=0.2, lns_min_remaining_seconds=0, min_lns_seconds=0))
    )
    cp_sat = grouped["cp_sat"]

    assert "phases" not in grouped["timing"]
    assert "phase1" in cp_sat["phases"]
    assert "phase2" in cp_sat["phases"]

    assert "best_objective_over_time_points" in cp_sat
    assert "best_objective_over_time_points" not in grouped["timing"]["global"]

    phase1 = cp_sat["phases"]["phase1"]
    for key in ["phase1_time_limit_seconds", "phase1_wall_time_seconds", "phase1_solve_wall_time_seconds", "phase1_status_raw", "phase1_normalized_status", "phase1_best_objective_value", "phase1_understaff_total_unweighted", "phase1_coverage_ratio_unweighted"]:
        assert key in phase1

    phase2 = cp_sat["phases"]["phase2"]
    for key in ["phase2_model_rebuild_wall_time_seconds", "phase2_reused_model", "phase2_solve_wall_time_seconds", "phase2_time_limit_seconds", "phase2_wall_time_seconds", "phase2_status_raw", "phase2_normalized_status", "phase2_best_objective_value", "phase2_non_regression_constraint_applied", "phase2_non_regression_bound", "phase2_understaff_total_unweighted", "phase2_coverage_ratio_unweighted"]:
        assert key in phase2


def test_phase2_budget_reporting_and_solver_max_applied_are_sane():
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                start_date=date(2026, 1, 1),
                end_date=date(2026, 1, 6),
                time_limit_seconds=2,
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=2, poste_id=1) for d in range(1, 7)],
                v3_strategy="two_phase_lns",
                lns_iter_seconds=0.2,
                lns_min_remaining_seconds=0,
                min_lns_seconds=0,
            )
        )
    )
    phase2 = grouped["cp_sat"]["phases"]["phase2"]
    assert phase2["phase2_time_limit_seconds"] >= 0
    remaining = phase2.get("phase2_remaining_after_phase1_seconds")
    if remaining is not None:
        assert remaining >= phase2["phase2_time_limit_seconds"]

    assert grouped["timing"]["global"]["solver_max_time_seconds_applied"] >= 0


def test_solver_max_time_seconds_applied_not_overwritten_when_no_time_limit():
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                time_limit_seconds=0,
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1, poste_id=1)],
                v3_strategy="two_phase",
            )
        )
    )
    assert grouped["timing"]["global"]["solver_max_time_seconds_applied"] > 0


def test_existing_absent_and_leave_are_hard_overrides():
    out = OrtoolsSolver().generate(
        _build_input(
            agent_ids=[1],
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            existing_daytype_by_agent_day_ctx={
                (1, date(2026, 1, 1)): "leave",
                (1, date(2026, 1, 2)): "absent",
            },
            existing_day_type_by_agent_day={
                (1, date(2026, 1, 1)): "leave",
                (1, date(2026, 1, 2)): "absent",
            },
            coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1, poste_id=1)],
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            seed=42,
        )
    )
    day_types = {(d.agent_id, d.day_date): d.day_type for d in out.agent_days}
    assert day_types[(1, date(2026, 1, 1))] == "leave"
    assert day_types[(1, date(2026, 1, 2))] == "absent"
    assert all(a.day_date not in {date(2026, 1, 1), date(2026, 1, 2)} for a in out.assignments)


def test_existing_change_penalties_and_feature_flag_toggle():
    base_kwargs = dict(
        agent_ids=[1],
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        seed=42,
        qualified_postes_by_agent={1: (1,)},
        qualification_date_by_agent_poste={(1, 1): None},
        existing_daytype_by_agent_day_ctx={(1, date(2026, 1, 1)): "rest"},
        coverage_demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1, poste_id=1)],
    )
    with_flag = _grouped(OrtoolsSolver().generate(_build_input(**base_kwargs)))
    no_flag = _grouped(OrtoolsSolver().generate(_build_input(**{**base_kwargs, "use_existing_assignments": False})))
    assert with_flag["solution_quality"]["existing_change_strong_total"] >= 1
    assert no_flag["solution_quality"]["existing_change_strong_total"] == 0


def test_existing_working_combo_change_and_zcot_transitions_penalties():
    day = date(2026, 1, 1)
    # Unknown existing working signature + forced working day => medium change penalty.
    inp = _build_input(
        agent_ids=[1],
        start_date=day,
        end_date=day,
        seed=42,
        qualified_postes_by_agent={1: (1,)},
        qualification_date_by_agent_poste={(1, 1): None},
        existing_daytype_by_agent_day_ctx={(1, day): "working"},
        existing_assignment_by_agent_day_ctx={(1, day): {"poste_id": 999, "tranche_ids": (999,)}},
        coverage_demands=[CoverageDemand(day_date=day, tranche_id=10, required_count=1, poste_id=1)],
    )
    grouped = _grouped(OrtoolsSolver().generate(inp))
    assert grouped["solution_quality"]["existing_change_medium_total"] >= 1

    zcot_work = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                agent_ids=[1],
                start_date=day,
                end_date=day,
                seed=42,
                existing_daytype_by_agent_day_ctx={(1, day): "zcot"},
                coverage_demands=[CoverageDemand(day_date=day, tranche_id=10, required_count=1, poste_id=1)],
                qualified_postes_by_agent={1: (1,)},
                qualification_date_by_agent_poste={(1, 1): None},
            )
        )
    )
    assert zcot_work["solution_quality"]["existing_change_strong_total"] == 0
    assert zcot_work["solution_quality"]["existing_change_medium_total"] == 0

    zcot_rest = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                agent_ids=[1],
                start_date=day,
                end_date=day,
                seed=42,
                existing_daytype_by_agent_day_ctx={(1, day): "zcot"},
                coverage_demands=[],
                absences={(1, day)},
                qualified_postes_by_agent={1: (1,)},
                qualification_date_by_agent_poste={(1, 1): None},
            )
        )
    )
    assert zcot_rest["solution_quality"]["existing_change_medium_total"] >= 1


def test_existing_assignments_conflict_resolution_and_audit():
    day = date(2026, 1, 1)
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                agent_ids=[1],
                start_date=day,
                end_date=day,
                seed=42,
                absences={(1, day)},
                existing_daytype_by_agent_day_ctx={(1, day): "working"},
                existing_assignment_by_agent_day_ctx={(1, day): {"poste_id": 1, "tranche_ids": (10,)}},
                qualified_postes_by_agent={1: (1,)},
                qualification_date_by_agent_poste={(1, 1): None},
                coverage_demands=[CoverageDemand(day_date=day, tranche_id=10, required_count=1, poste_id=1)],
            )
        )
    )
    assert grouped["model"]["existing_assignments_conflicts_count"] == 1
    sample = grouped["model"]["existing_assignments_conflicts_sample"]
    assert sample
    assert sample[0]["agent_id"] == 1
    assert sample[0]["day_date"] == day.isoformat()
    assert sample[0]["conflict_reason"] == "solver_absence_conflicts_with_db_daytype"


def test_existing_change_penalty_is_in_window_only_with_context_days():
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                agent_ids=[1],
                start_date=date(2026, 1, 2),
                end_date=date(2026, 1, 2),
                seed=42,
                existing_daytype_by_agent_day_ctx={
                    (1, date(2026, 1, 1)): "working",
                    (1, date(2026, 1, 3)): "working",
                },
                existing_assignment_by_agent_day_ctx={
                    (1, date(2026, 1, 1)): {"poste_id": 1, "tranche_ids": (10,)},
                    (1, date(2026, 1, 3)): {"poste_id": 1, "tranche_ids": (10,)},
                },
                qualified_postes_by_agent={1: (1,)},
                qualification_date_by_agent_poste={(1, 1): None},
                coverage_demands=[],
            )
        )
    )
    assert grouped["solution_quality"]["existing_change_strong_total"] == 0
    assert grouped["solution_quality"]["existing_change_medium_total"] == 0


def test_existing_unknown_working_signature_audited_and_non_crashing():
    day = date(2026, 1, 1)
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                agent_ids=[1],
                start_date=day,
                end_date=day,
                seed=42,
                qualified_postes_by_agent={1: (1,)},
                qualification_date_by_agent_poste={(1, 1): None},
                existing_daytype_by_agent_day_ctx={(1, day): "working"},
                existing_assignment_by_agent_day_ctx={(1, day): {"poste_id": 999, "tranche_ids": (999,)}},
                coverage_demands=[CoverageDemand(day_date=day, tranche_id=10, required_count=1, poste_id=1)],
            )
        )
    )
    assert grouped["model"]["existing_working_signature_unknown_count"] >= 1
    assert grouped["model"]["existing_working_signature_unknown_sample"]


def test_existing_penalty_dominance_observability_ratios_present_and_sane():
    grouped = _grouped(OrtoolsSolver().generate(_build_input(seed=42)))
    ratios = grouped["objective"]["dominance_ratios"]
    for key in [
        "max_cost_existing_change_strong",
        "max_cost_existing_change_medium",
        "ratio_existing_change_strong_vs_one_understaff_weekday_day",
        "ratio_existing_change_medium_vs_one_understaff_weekday_day",
    ]:
        assert key in ratios
    assert ratios["ratio_existing_change_strong_vs_one_understaff_weekday_day"] > 0
    assert ratios["ratio_existing_change_medium_vs_one_understaff_weekday_day"] > 0
    assert ratios["ratio_existing_change_strong_vs_one_understaff_weekday_day"] < 1
    assert ratios["ratio_existing_change_medium_vs_one_understaff_weekday_day"] < 1


def assert_min_rest_after_six_workdays(agent_days, assignments, combos_by_day, context_dates, min_gap_minutes=3620):
    assignment_set = {(a.agent_id, a.day_date, a.tranche_id) for a in assignments}
    day_type_map = {(d.agent_id, d.day_date): d.day_type for d in agent_days}

    by_agent = {}
    for d in agent_days:
        by_agent.setdefault(d.agent_id, set()).add(d.day_date)

    for agent_id in by_agent:
        timeline = []
        for i, day in enumerate(context_dates):
            combo = combos_by_day.get(day)
            worked = False
            start_abs = None
            end_abs = None
            combo_id = None
            if combo is not None and day_type_map.get((agent_id, day)) == "working":
                if any((agent_id, day, tranche_id) in assignment_set for tranche_id in combo["tranche_ids"]):
                    worked = True
                    start_abs = i * 1440 + combo["start_min"]
                    end_abs = i * 1440 + combo["end_min"]
                    combo_id = combo["id"]
            timeline.append({"worked": worked, "start_abs": start_abs, "end_abs": end_abs, "combo_id": combo_id, "day": day})

        for s in range(0, max(0, len(timeline) - 5)):
            if not all(timeline[s + k]["worked"] for k in range(6)):
                continue
            last = timeline[s + 5]
            next_work = next((timeline[u] for u in range(s + 6, len(timeline)) if timeline[u]["worked"]), None)
            if next_work is None:
                continue
            gap = next_work["start_abs"] - last["end_abs"]
            assert gap >= min_gap_minutes, (
                f"agent={agent_id} last_day={last['day']} next_day={next_work['day']} gap={gap} "
                f"last_combo_id={last['combo_id']} next_combo_id={next_work['combo_id']}"
            )


def test_rpdouble_requires_3620_min_gap_after_6_worked_days_day_shift():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    end = date(2026, 1, 8)
    days = [start.fromordinal(start.toordinal() + i) for i in range((end - start).days + 1)]
    demands = [CoverageDemand(day_date=d, tranche_id=10, required_count=1, poste_id=1) for d in days]

    out = solver.generate(
        _build_input(
            agent_ids=[1],
            start_date=start,
            end_date=end,
            seed=123,
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(16, 0))],
            coverage_demands=demands,
            gpt_context_days=days,
        )
    )

    combos_by_day = {d: {"id": 10, "tranche_ids": (10,), "start_min": 8 * 60, "end_min": 16 * 60} for d in days}
    assert_min_rest_after_six_workdays(out.agent_days, out.assignments, combos_by_day, days, min_gap_minutes=3620)
    grouped = _grouped(out)
    assert grouped["solution_quality"]["rpdouble_gap_minutes_required"] == 3620
    assert grouped["solution_quality"]["rpdouble_gap_violation_count_total"] == 0


def test_rpdouble_requires_3620_min_gap_after_6_worked_days_late_shift():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    end = date(2026, 1, 10)
    days = [start.fromordinal(start.toordinal() + i) for i in range((end - start).days + 1)]
    demands = [CoverageDemand(day_date=d, tranche_id=20, required_count=1, poste_id=1) for d in days]

    out = solver.generate(
        _build_input(
            agent_ids=[1],
            start_date=start,
            end_date=end,
            seed=123,
            qualified_postes_by_agent={1: (1,)},
            qualification_date_by_agent_poste={(1, 1): None},
            tranches=[TrancheInfo(id=20, poste_id=1, heure_debut=time(17, 0), heure_fin=time(1, 0))],
            coverage_demands=demands,
            gpt_context_days=days,
        )
    )

    combos_by_day = {d: {"id": 20, "tranche_ids": (20,), "start_min": 17 * 60, "end_min": (24 + 1) * 60} for d in days}
    assert_min_rest_after_six_workdays(out.agent_days, out.assignments, combos_by_day, days, min_gap_minutes=3620)
    grouped = _grouped(out)
    assert grouped["solution_quality"]["rpdouble_gap_minutes_required"] == 3620
    assert grouped["solution_quality"]["rpdouble_gap_violation_count_total"] == 0


def test_existing_working_missing_assignments_is_audited_and_not_counted_as_rpdouble_worked():
    grouped = _grouped(
        OrtoolsSolver().generate(
            _build_input(
                agent_ids=[1],
                start_date=date(2026, 1, 2),
                end_date=date(2026, 1, 8),
                seed=42,
                qualified_postes_by_agent={1: (1,)},
                qualification_date_by_agent_poste={(1, 1): None},
                gpt_context_days=[date(2026, 1, d) for d in range(1, 9)],
                existing_daytype_by_agent_day_ctx={(1, date(2026, 1, 1)): "working"},
                existing_assignment_by_agent_day_ctx={(1, date(2026, 1, 1)): {"poste_id": 1, "tranche_ids": ()}},
                existing_shift_start_end_by_agent_day_ctx={(1, date(2026, 1, 1)): (8 * 60, 16 * 60)},
                coverage_demands=[CoverageDemand(day_date=date(2026, 1, d), tranche_id=10, required_count=1, poste_id=1) for d in range(2, 9)],
            )
        )
    )
    assert grouped["model"]["existing_working_missing_assignments_count_total"] == 1
    assert grouped["model"]["existing_working_missing_assignments_sample"]
    assert grouped["model"]["existing_working_missing_assignments_sample"][0]["day_date"] == "2026-01-01"
    assert grouped["solution_quality"]["rpdouble_gap_violation_count_total"] == 0
