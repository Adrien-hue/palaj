from __future__ import annotations

from backend.app.services.solver.ortools_solver import OrtoolsSolver
from backend.app.services.solver.rh_combos import DayCombo, DayKind, shift_involves_night


def test_shift_involves_night_morning_window():
    assert shift_involves_night(5 * 60, 9 * 60) is True


def test_shift_involves_night_evening_window():
    assert shift_involves_night(20 * 60, 22 * 60) is True


def test_shift_involves_night_daytime_false():
    assert shift_involves_night(7 * 60, 15 * 60) is False


def test_shift_involves_night_crosses_midnight():
    assert shift_involves_night(22 * 60, 24 * 60 + 6 * 60 + 30) is True


def test_shift_involves_night_boundary_end_exclusive():
    assert shift_involves_night(6 * 60 + 30, 7 * 60) is False


def test_day_kind_helpers_zcot_not_rest():
    zcot_combo = DayCombo(
        id=99,
        poste_id=None,
        tranche_ids=(),
        start_min=None,
        end_min=None,
        work_minutes=0,
        amplitude_minutes=0,
        involves_night=False,
        day_kind=DayKind.ZCOT,
    )

    assert OrtoolsSolver._is_rest_combo(zcot_combo) is False
    assert OrtoolsSolver._is_work_combo(zcot_combo) is True
    assert OrtoolsSolver._is_off_for_rpdouble_combo(zcot_combo) is False
