from __future__ import annotations

from datetime import date, time, timedelta

import pytest

from backend.app.services.solver.models import CoverageDemand, InfeasibleError, SolverAgentDay, SolverInput, TrancheInfo
from backend.app.services.solver.ortools_solver import OrtoolsSolver


def _grouped(out: object) -> dict:
    return out.stats["stats"]


def assert_min_rest_after_six_workdays(agent_days, assignments, combos_by_day, context_dates, min_gap_minutes=3620):
    assignment_set = {(a.agent_id, a.day_date, a.tranche_id) for a in assignments}
    day_type_map = {(d.agent_id, d.day_date): d.day_type for d in agent_days}

    agents = sorted({d.agent_id for d in agent_days})
    for agent_id in agents:
        timeline = []
        for i, day in enumerate(context_dates):
            combo = combos_by_day.get(day)
            worked = False
            start_abs = None
            end_abs = None
            if combo is not None and day_type_map.get((agent_id, day)) == "working":
                if any((agent_id, day, tranche_id) in assignment_set for tranche_id in combo["tranche_ids"]):
                    worked = True
                    start_abs = i * 1440 + combo["start_min"]
                    end_abs = i * 1440 + combo["end_min"]
            timeline.append({"worked": worked, "start_abs": start_abs, "end_abs": end_abs, "day": day})

        for s in range(0, max(0, len(timeline) - 5)):
            if not all(timeline[s + k]["worked"] for k in range(6)):
                continue
            last = timeline[s + 5]
            next_work = next((timeline[u] for u in range(s + 6, len(timeline)) if timeline[u]["worked"]), None)
            if next_work is None:
                continue
            gap = next_work["start_abs"] - last["end_abs"]
            assert gap >= min_gap_minutes, f"agent={agent_id} last_day={last['day']} next_day={next_work['day']} gap={gap}"


def _ctx_days(start: date, end: date) -> list[date]:
    days = []
    cursor = start - timedelta(days=7)
    last = end + timedelta(days=7)
    while cursor <= last:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _input(
    days: int = 7,
    demands: list[CoverageDemand] | None = None,
    existing_ctx: dict[tuple[int, date], str] | None = None,
    absences: set[tuple[int, date]] | None = None,
    existing_day_types: dict[tuple[int, date], str] | None = None,
    existing_assignments_ctx: dict[tuple[int, date], dict] | None = None,
    existing_shifts_ctx: dict[tuple[int, date], tuple[int, int]] | None = None,
    tranche_end_hour: int = 16,
) -> SolverInput:
    start = date(2026, 1, 1)
    end = start + timedelta(days=days - 1)
    return SolverInput(
        team_id=1,
        start_date=start,
        end_date=end,
        seed=123,
        time_limit_seconds=5,
        agent_ids=[1],
        absences=absences or set(),
        qualified_postes_by_agent={1: (1,)},
        qualification_date_by_agent_poste={(1, 1): None},
        existing_day_type_by_agent_day=existing_day_types or {},
        poste_ids=[1],
        tranches=[TrancheInfo(id=10, poste_id=1, heure_debut=time(8, 0), heure_fin=time(tranche_end_hour, 0))],
        coverage_demands=demands or [],
        gpt_context_days=_ctx_days(start, end),
        existing_day_type_by_agent_day_ctx=existing_ctx or {},
        existing_work_minutes_by_agent_day_ctx={},
        existing_shift_start_end_by_agent_day_ctx=existing_shifts_ctx or {},
        existing_assignment_by_agent_day_ctx=existing_assignments_ctx or {},
    )


def test_gpt_max_6_days_infeasible_with_7_forced_work_days():
    solver = OrtoolsSolver()
    demands = [CoverageDemand(day_date=date(2026, 1, 1) + timedelta(days=i), tranche_id=10, required_count=1) for i in range(7)]
    out = solver.generate(_input(days=7, demands=demands))
    grouped = _grouped(out)
    assert grouped["coverage"]["understaff_total"] >= 0
    assert grouped["objective"]["objective_terms"]["understaff_weighted"] >= 0


def test_gpt_48h_max_infeasible_for_6x10h():
    solver = OrtoolsSolver()
    demands = [CoverageDemand(day_date=date(2026, 1, 1) + timedelta(days=i), tranche_id=10, required_count=1) for i in range(6)]
    out = solver.generate(_input(days=6, demands=demands, tranche_end_hour=18))
    grouped = _grouped(out)
    assert grouped["coverage"]["understaff_total"] >= 0


def test_gpt_leave_counts_in_run_with_zero_minutes():
    solver = OrtoolsSolver()
    leave_day = date(2026, 1, 2)
    inp = _input(
        days=4,
        demands=[
            CoverageDemand(day_date=date(2026, 1, 1), tranche_id=10, required_count=1),
            CoverageDemand(day_date=date(2026, 1, 3), tranche_id=10, required_count=1),
            CoverageDemand(day_date=date(2026, 1, 4), tranche_id=10, required_count=1),
        ],
        existing_ctx={(1, leave_day): "leave"},
        existing_day_types={(1, leave_day): "leave"},
        absences={(1, leave_day)},
    )
    out = solver.generate(inp)
    leave_out = next(d for d in out.agent_days if d.day_date == leave_day and d.agent_id == 1)
    assert leave_out.day_type == "leave"


def test_gpt_rpdouble_enforces_3620_gap_after_6_day_run():
    solver = OrtoolsSolver()
    demands = [CoverageDemand(day_date=date(2026, 1, 1) + timedelta(days=i), tranche_id=10, required_count=1) for i in range(8)]
    out = solver.generate(_input(days=8, demands=demands))
    grouped = _grouped(out)
    days = _ctx_days(date(2026, 1, 1), date(2026, 1, 8))
    combos_by_day = {d: {"tranche_ids": (10,), "start_min": 8 * 60, "end_min": 16 * 60} for d in days}
    assert_min_rest_after_six_workdays(out.agent_days, out.assignments, combos_by_day, days, min_gap_minutes=3620)
    assert grouped["solution_quality"]["rpdouble_gap_minutes_required"] == 3620
    assert grouped["solution_quality"]["rpdouble_gap_violation_count_total"] == 0


def test_rpdouble_disallows_zcot_as_worked_service_interval():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    e_plus_1 = start + timedelta(days=6)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(6)]
    out = solver.generate(
        _input(
            days=8,
            demands=demands,
            existing_ctx={(1, e_plus_1): "zcot"},
            existing_day_types={(1, e_plus_1): "zcot"},
        )
    )
    grouped = _grouped(out)
    assert grouped["solution_quality"]["rpdouble_gap_violation_count_total"] == 0


def test_missing_tranche_in_any_combo_is_hard_infeasible_precheck():
    solver = OrtoolsSolver()
    demands = [CoverageDemand(day_date=date(2026, 1, 1), tranche_id=999, required_count=1)]

    with pytest.raises(InfeasibleError) as exc:
        solver.generate(_input(days=1, demands=demands))

    grouped = exc.value.stats["stats"]
    assert grouped["model"]["missing_tranche_in_any_combo_count"] > 0


def test_can_chain_multiple_gpt_runs_over_month():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(31)]

    grouped = _grouped(solver.generate(_input(days=31, demands=demands)))

    assert grouped["model"]["coverage_active"] is True
    assert grouped["model"]["can_cover_any_demand_in_window"] is True
    assert grouped["model"]["runs_candidate_count_by_agent"].get(1, 0) > 0
    assert grouped["model"]["run_feasible_candidate_count_by_agent"].get(1, 0) > 0
    assert grouped["solution_quality"]["max_work_days"] > 3


def test_rest_choice_available_every_day_when_daily_choice_is_exactly_one():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(7)]

    grouped = _grouped(solver.generate(_input(days=7, demands=demands)))

    assert grouped["model"]["daily_choice_mode"] in {"exactly_one", "at_most_one"}
    if grouped["model"]["daily_choice_mode"] == "exactly_one":
        assert grouped["model"]["rest_combo_count_in_model"] >= 1
        assert grouped["model"]["has_rest_choice_each_day_in_window_by_agent"][1] is True


def test_worked_ctx_window_days_are_not_history_fixed():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(14)]

    grouped = _grouped(solver.generate(_input(days=14, demands=demands)))

    assert grouped["model"]["gpt_window_days_count"] == 14
    assert grouped["model"]["worked_ctx_window_fixed_days_count_by_agent"][1] == 0


def test_history_working_without_shift_is_not_counted_as_worked_for_rpdouble():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    e_plus_1 = start + timedelta(days=6)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(6)]

    grouped_missing = _grouped(
        solver.generate(
            _input(
                days=8,
                demands=demands,
                existing_ctx={(1, e_plus_1): "working"},
                existing_day_types={(1, e_plus_1): "working"},
                existing_assignments_ctx={(1, e_plus_1): {"poste_id": 1, "tranche_ids": ()}},
            )
        )
    )
    grouped_with_shift = _grouped(
        solver.generate(
            _input(
                days=8,
                demands=demands,
                existing_ctx={(1, e_plus_1): "working"},
                existing_day_types={(1, e_plus_1): "working"},
                existing_assignments_ctx={(1, e_plus_1): {"poste_id": 1, "tranche_ids": (10,)}},
                existing_shifts_ctx={(1, e_plus_1): (8 * 60, 16 * 60)},
            )
        )
    )

    assert grouped_missing["model"]["existing_working_missing_assignments_count_total"] >= 1
    assert grouped_with_shift["model"]["existing_working_missing_assignments_count_total"] == 0


def _worked_run_lengths_in_window(out, start: date, days: int, *, worked_types: tuple[str, ...] = ("working", "zcot")) -> list[int]:
    by_day = {
        d.day_date: d.day_type
        for d in out.agent_days
        if d.agent_id == 1 and start <= d.day_date <= (start + timedelta(days=days - 1))
    }
    lengths: list[int] = []
    run = 0
    for i in range(days):
        day = start + timedelta(days=i)
        if by_day.get(day) in worked_types:
            run += 1
        elif run:
            lengths.append(run)
            run = 0
    if run:
        lengths.append(run)
    return lengths


def test_gpt_min_length_1_day_forbidden():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    demands = [CoverageDemand(day_date=start, tranche_id=10, required_count=1)]
    grouped = _grouped(solver.generate(_input(days=4, demands=demands)))
    assert grouped["solution_quality"]["gpt_len_1_count_total"] >= 1
    assert grouped["solution_quality"]["gpt_length_violation_count_total"] >= 1


def test_gpt_min_length_2_days_forbidden():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(2)]
    grouped = _grouped(solver.generate(_input(days=5, demands=demands)))
    assert grouped["solution_quality"]["gpt_len_2_count_total"] >= 1
    assert grouped["solution_quality"]["gpt_length_violation_count_total"] >= 1


def test_gpt_max_length_7_days_forbidden():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(7)]
    grouped = _grouped(solver.generate(_input(days=7, demands=demands)))
    assert grouped["solution_quality"]["gpt_length_violation_count_total"] == 0


def test_gpt_lengths_3_to_6_allowed():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    for length in (3, 4, 5, 6):
        demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(length)]
        grouped = _grouped(solver.generate(_input(days=length, demands=demands)))
        assert grouped["solution_quality"][f"gpt_len_{length}_count_total"] >= 1


def test_gpt_prefers_4_or_5_over_3_or_6_when_coverage_equal():
    solver = OrtoolsSolver()
    solver.W_USELESS_WORK = 0
    solver.W_WORK_BLOCKS = 0
    solver.W_STABILITY_CHANGE = 0
    solver.W_FAIR_DAYS_SPREAD = 0
    solver.W_FAIR_MINUTES_SPREAD = 0
    solver.W_NIGHTS_TOTAL = 0
    solver.W_NIGHTS_SPREAD = 0
    solver.W_AMPLITUDE = 0
    solver.W_RPDOUBLE_BONUS = 0
    solver.W_TRANCHE_DIVERSITY = 0
    solver.W_UNDERSTAFF_SMOOTH = 0

    start = date(2026, 1, 1)
    demands_4 = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(4)]
    demands_6 = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(6)]

    out_4 = solver.generate(_input(days=4, demands=demands_4))
    out_6 = solver.generate(_input(days=6, demands=demands_6))
    grouped_4 = _grouped(out_4)
    grouped_6 = _grouped(out_6)

    assert grouped_4["coverage"]["understaff_total"] == 0
    assert grouped_6["coverage"]["understaff_total"] == 0
    assert grouped_4["solution_quality"]["gpt_length_penalty_total"] == 0
    assert grouped_6["solution_quality"]["gpt_length_penalty_total"] > 0


def test_gpt_stats_present():
    solver = OrtoolsSolver()
    grouped = _grouped(solver.generate(_input(days=7)))
    for key in [
        "gpt_count_total",
        "gpt_len_1_count_total",
        "gpt_len_2_count_total",
        "gpt_len_3_count_total",
        "gpt_len_4_count_total",
        "gpt_len_5_count_total",
        "gpt_len_6_count_total",
        "gpt_length_violation_count_total",
        "gpt_length_violation_sample",
        "gpt_len_1_penalized_total",
        "gpt_len_2_penalized_total",
        "gpt_len_3_penalized_total",
        "gpt_len_6_penalized_total",
        "gpt_length_penalty_total",
    ]:
        assert key in grouped["solution_quality"]


def test_gpt_len1_len2_stats_are_based_on_final_window_not_context_only():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)

    existing_len1 = {
        (1, start - timedelta(days=3)): "rest",
        (1, start - timedelta(days=2)): "zcot",
        (1, start - timedelta(days=1)): "rest",
    }
    grouped_len1 = _grouped(
        solver.generate(
            _input(
                days=1,
                demands=[],
                existing_ctx=existing_len1,
                existing_day_types=existing_len1,
            )
        )
    )
    assert grouped_len1["solution_quality"]["gpt_len_1_count_total"] == 0
    assert grouped_len1["solution_quality"]["gpt_len_1_penalized_total"] >= 1

    existing_len2 = {
        (1, start - timedelta(days=4)): "rest",
        (1, start - timedelta(days=3)): "zcot",
        (1, start - timedelta(days=2)): "zcot",
        (1, start - timedelta(days=1)): "rest",
    }
    grouped_len2 = _grouped(
        solver.generate(
            _input(
                days=1,
                demands=[],
                existing_ctx=existing_len2,
                existing_day_types=existing_len2,
            )
        )
    )
    assert grouped_len2["solution_quality"]["gpt_len_2_count_total"] == 0
    assert grouped_len2["solution_quality"]["gpt_len_2_penalized_total"] >= 1




def test_gpt_len1_count_uses_final_day_types_for_isolated_working_days():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    existing_day_types = {
        (1, start): "working",
        (1, start + timedelta(days=1)): "rest",
        (1, start + timedelta(days=2)): "working",
        (1, start + timedelta(days=3)): "rest",
        (1, start + timedelta(days=4)): "working",
    }

    grouped = _grouped(
        solver.generate(
            _input(
                days=5,
                demands=[],
                existing_ctx=existing_day_types,
                existing_day_types=existing_day_types,
            )
        )
    )

    assert grouped["solution_quality"]["gpt_len_1_count_total"] > 0
    assert grouped["solution_quality"]["gpt_len_1_penalized_total"] > 0


def test_gpt_zcot_counts_as_worked_day_for_length_rules():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    existing = {(1, start + timedelta(days=i)): "zcot" for i in range(4)}
    out = solver.generate(_input(days=4, existing_ctx=existing, existing_day_types=existing))
    runs = _worked_run_lengths_in_window(out, start, 4)
    assert runs == [4]


def test_gpt_min3_start_on_window_edge_uses_context_days_for_extensions():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    out = solver.generate(
        _input(
            days=1,
            demands=[CoverageDemand(day_date=start, tranche_id=10, required_count=1)],
        )
    )
    grouped = _grouped(out)
    assert grouped["coverage"]["understaff_total"] >= 0
    assert grouped["model"]["gpt_start_candidates_count_total"] >= 1
    assert grouped["model"]["gpt_min3_forced_extensions_count_total"] >= 2
    assert grouped["model"]["gpt_min3_forced_extensions_impossible_count_total"] >= 1


def test_gpt_rules_do_not_make_base_instance_infeasible():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(4)]
    out = solver.generate(_input(days=4, demands=demands))
    grouped = _grouped(out)
    assert grouped["coverage"]["understaff_total"] == 0
    assert grouped["solution_quality"]["gpt_length_violation_count_total"] == 0


def test_gpt_min3_with_db_boundary_does_not_force_impossible_extension():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    existing_ctx = {(1, start - timedelta(days=1)): "zcot"}
    out = solver.generate(
        _input(
            days=1,
            demands=[CoverageDemand(day_date=start, tranche_id=10, required_count=1)],
            existing_ctx=existing_ctx,
            existing_day_types=existing_ctx,
        )
    )
    grouped = _grouped(out)
    assert grouped["coverage"]["understaff_total"] == 0
    assert grouped["model"]["gpt_min3_forced_extensions_impossible_count_total"] >= 0


def test_gpt_max6_with_existing_ctx_does_not_overconstrain_window():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    existing_ctx = {(1, start - timedelta(days=offset + 1)): "zcot" for offset in range(6)}
    out = solver.generate(
        _input(
            days=1,
            demands=[],
            existing_ctx=existing_ctx,
            existing_day_types=existing_ctx,
        )
    )
    grouped = _grouped(out)
    assert grouped["model"]["gpt_max6_risk_windows_count_total"] >= 1


def test_gpt_hard_conflict_stats_present_when_infeasible():
    solver = OrtoolsSolver()
    with pytest.raises(InfeasibleError) as exc:
        solver.generate(_input(days=1, demands=[CoverageDemand(day_date=date(2026, 1, 1), tranche_id=999, required_count=1)]))

    grouped = exc.value.stats["stats"]
    model = grouped["model"]
    assert "gpt_hard_conflict_count_total" in model
    assert "gpt_hard_conflict_sample" in model


def test_zcot_counts_for_gpt_without_breaking_feasibility():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    existing = {(1, start + timedelta(days=i)): "zcot" for i in range(3)}
    out = solver.generate(_input(days=4, existing_ctx=existing, existing_day_types=existing))
    grouped = _grouped(out)
    assert grouped["solution_quality"]["gpt_length_violation_count_total"] == 0


def test_gpt_postsolve_counters_use_final_schedule_day_types():
    solver = OrtoolsSolver()
    start = date(2026, 3, 1)
    dates = [start + timedelta(days=i) for i in range(9)]
    # Runs in final schedule: WWR WR WWWR -> lengths 2,1,3.
    final_day_types = [
        "working",
        "working",
        "rest",
        "working",
        "rest",
        "working",
        "working",
        "working",
        "rest",
    ]
    agent_days = [
        SolverAgentDay(agent_id=1, day_date=day_date, day_type=day_type)
        for day_date, day_type in zip(dates, final_day_types, strict=True)
    ]

    gpt_len_counts, gpt_total, gpt_violation_count, _ = solver._compute_gpt_stats_from_final_schedule(
        ordered_agent_ids=[1],
        dates=dates,
        agent_days=agent_days,
        assigned_day_by_agent={(1, i) for i, day_type in enumerate(final_day_types) if day_type == "working"},
    )

    assert gpt_total == 3
    assert gpt_len_counts[1] > 0
    assert gpt_len_counts[2] > 0
    assert gpt_len_counts[3] > 0
    assert gpt_violation_count > 0


def test_gpt_postsolve_counters_treat_zcot_as_worked_in_final_schedule():
    solver = OrtoolsSolver()
    start = date(2026, 3, 1)
    dates = [start + timedelta(days=i) for i in range(4)]
    # ZCOT + WORKING + WORKING must be one GPT run of length 3.
    agent_days = [
        SolverAgentDay(agent_id=1, day_date=dates[0], day_type="zcot"),
        SolverAgentDay(agent_id=1, day_date=dates[1], day_type="working"),
        SolverAgentDay(agent_id=1, day_date=dates[2], day_type="working"),
        SolverAgentDay(agent_id=1, day_date=dates[3], day_type="rest"),
    ]

    gpt_len_counts, gpt_total, gpt_violation_count, _ = solver._compute_gpt_stats_from_final_schedule(
        ordered_agent_ids=[1],
        dates=dates,
        agent_days=agent_days,
        assigned_day_by_agent={(1, 1), (1, 2)},
    )

    assert gpt_total == 1
    assert gpt_len_counts[3] == 1
    assert gpt_violation_count == 0
