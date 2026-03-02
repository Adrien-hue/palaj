from __future__ import annotations

from datetime import date, time, timedelta

import pytest

from backend.app.services.solver.models import CoverageDemand, InfeasibleError, SolverInput, TrancheInfo
from backend.app.services.solver.ortools_solver import OrtoolsSolver


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
        existing_shift_start_end_by_agent_day_ctx={},
    )




def test_gpt_min_3_days_extends_run_when_only_2_days_are_forced():
    solver = OrtoolsSolver()
    demands = [
        CoverageDemand(day_date=date(2026, 1, 2), tranche_id=10, required_count=1),
        CoverageDemand(day_date=date(2026, 1, 3), tranche_id=10, required_count=1),
    ]
    out = solver.generate(_input(days=4, demands=demands))
    worked_days = {a.day_date for a in out.assignments}
    assert len(worked_days) >= 3


def test_gpt_max_6_days_infeasible_with_7_forced_work_days():
    solver = OrtoolsSolver()
    demands = [CoverageDemand(day_date=date(2026, 1, 1) + timedelta(days=i), tranche_id=10, required_count=1) for i in range(7)]
    with pytest.raises(InfeasibleError):
        solver.generate(_input(days=7, demands=demands))


def test_gpt_48h_max_infeasible_for_6x10h():
    solver = OrtoolsSolver()
    demands = [CoverageDemand(day_date=date(2026, 1, 1) + timedelta(days=i), tranche_id=10, required_count=1) for i in range(6)]
    with pytest.raises(InfeasibleError):
        solver.generate(_input(days=6, demands=demands, tranche_end_hour=18))


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


def test_gpt_rp_double_blocks_work_on_next_day_after_6_day_run():
    solver = OrtoolsSolver()
    demands = [CoverageDemand(day_date=date(2026, 1, 1) + timedelta(days=i), tranche_id=10, required_count=1) for i in range(7)]
    with pytest.raises(InfeasibleError):
        solver.generate(_input(days=8, demands=demands))


def test_gpt_rp_double_ok_with_two_rest_days_after_6_day_run():
    solver = OrtoolsSolver()
    demands = [CoverageDemand(day_date=date(2026, 1, 1) + timedelta(days=i), tranche_id=10, required_count=1) for i in range(6)]
    demands.extend(
        [
            CoverageDemand(day_date=date(2026, 1, 9), tranche_id=10, required_count=1),
            CoverageDemand(day_date=date(2026, 1, 10), tranche_id=10, required_count=1),
            CoverageDemand(day_date=date(2026, 1, 11), tranche_id=10, required_count=1),
        ]
    )
    out = solver.generate(_input(days=11, demands=demands))
    assert len(out.assignments) >= 9
    assert out.stats["rpdouble_off_rule"] == "rest_only"


def test_rpdouble_disallows_zcot_as_off_day():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    e_plus_1 = start + timedelta(days=6)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(6)]
    with pytest.raises(InfeasibleError):
        solver.generate(
            _input(
                days=8,
                demands=demands,
                existing_ctx={(1, e_plus_1): "zcot"},
                existing_day_types={(1, e_plus_1): "zcot"},
            )
        )


def test_rpdouble_requires_rest_only():
    solver = OrtoolsSolver()
    start = date(2026, 1, 1)
    e_plus_1 = start + timedelta(days=6)
    e_plus_2 = start + timedelta(days=7)
    demands = [CoverageDemand(day_date=start + timedelta(days=i), tranche_id=10, required_count=1) for i in range(6)]
    with pytest.raises(InfeasibleError):
        solver.generate(
            _input(
                days=8,
                demands=demands,
                existing_ctx={(1, e_plus_1): "leave", (1, e_plus_2): "rest"},
                existing_day_types={(1, e_plus_1): "leave", (1, e_plus_2): "rest"},
                absences={(1, e_plus_1)},
            )
        )
