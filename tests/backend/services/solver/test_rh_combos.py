from __future__ import annotations

from backend.app.services.solver.rh_combos import shift_involves_night


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
