from __future__ import annotations

from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from core.domain.enums.day_type import DayType
from core.rh_rules.general.rule_duree_travail import DureeTravailRule
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_interval import RhInterval

pytestmark = [pytest.mark.unit, pytest.mark.rh]

def dt(d: date, hh: int, mm: int = 0) -> datetime:
    return datetime.combine(d, time(hh, mm))


@pytest.fixture()
def rule() -> DureeTravailRule:
    return DureeTravailRule()


@pytest.fixture()
def ctx():
    # On n'a pas besoin d'un RhContext réel ici : la règle ne s'en sert pas
    return SimpleNamespace()


def test_non_working_day_is_ok(rule: DureeTravailRule, ctx):
    day = RhDay(
        agent_id=1,
        day_date=date(2026, 2, 10),
        day_type=DayType.REST,
        intervals=[],
        forfait_minutes=None,
    )

    result = rule.check_day(ctx, day)

    assert result.is_valid is True
    assert result.violations == []


def test_working_day_below_min_creates_min_violation_and_has_datetimes(rule: DureeTravailRule, ctx):
    # 4h = 240 min < 330
    d = date(2026, 2, 10)
    intervals = [RhInterval(start=dt(d, 8, 0), end=dt(d, 12, 0))]

    day = RhDay(
        agent_id=1,
        day_date=d,
        day_type=DayType.WORKING,
        intervals=intervals,
        forfait_minutes=None,
    )

    result = rule.check_day(ctx, day)

    assert result.is_valid is False
    assert len(result.violations) == 1

    v = result.violations[0]
    assert v.code == "DUREE_TRAVAIL_MIN_INSUFFISANTE"
    assert v.rule_name == rule.name
    assert v.start_date == d
    assert v.end_date == d

    # La règle met start_dt/end_dt dans meta (et parfois aussi dans RhViolation selon ton error_v)
    meta = v.meta or {}
    assert meta["total_minutes"] == 240
    assert meta["min_minutes"] == rule.DUREE_MIN_MIN
    assert meta["start_dt"] == intervals[0].start
    assert meta["end_dt"] == intervals[0].end


def test_working_day_above_max_creates_max_violation(rule: DureeTravailRule, ctx):
    # 11h = 660 min > 600
    d = date(2026, 2, 10)
    intervals = [RhInterval(start=dt(d, 7, 0), end=dt(d, 18, 0))]

    day = RhDay(
        agent_id=1,
        day_date=d,
        day_type=DayType.WORKING,
        intervals=intervals,
        forfait_minutes=None,
    )

    result = rule.check_day(ctx, day)

    assert result.is_valid is False
    assert len(result.violations) == 1
    assert result.violations[0].code == "DUREE_TRAVAIL_MAX_DEPASSEE"


def test_night_work_above_night_max_creates_night_max_violation(rule: DureeTravailRule, ctx, monkeypatch):
    """
    On force le 'nocturne' via monkeypatch pour tester la branche max nuit
    sans dépendre des règles exactes de rh_day_is_nocturne().
    """
    monkeypatch.setattr(
        "core.rh_rules.general.rule_duree_travail.rh_day_is_nocturne",
        lambda _day: True,
    )

    d = date(2026, 2, 10)
    # 9h = 540 min > 510 (max nuit)
    start = dt(d, 22, 0)
    end = start + timedelta(hours=9)
    intervals = [RhInterval(start=start, end=end)]

    day = RhDay(
        agent_id=1,
        day_date=d,
        day_type=DayType.WORKING,
        intervals=intervals,
        forfait_minutes=None,
    )

    result = rule.check_day(ctx, day)

    assert result.is_valid is False
    assert len(result.violations) == 1
    assert result.violations[0].code == "DUREE_TRAVAIL_MAX_NUIT_DEPASSEE"


def test_zcot_forfait_day_without_intervals_is_ok_and_does_not_crash(rule: DureeTravailRule, ctx):
    """
    Cas clé: ZCOT est "working" mais forfaitaire (8h) et sans intervals.
    => worked_minutes doit valoir 480 via forfait_minutes
    => la règle ne doit pas crasher (min/max sur empty) et doit être OK.
    """
    d = date(2026, 2, 10)

    day = RhDay(
        agent_id=1,
        day_date=d,
        day_type=DayType.ZCOT,
        intervals=[],
        forfait_minutes=8 * 60,
    )

    result = rule.check_day(ctx, day)

    assert result.is_valid is True
    assert result.violations == []


def test_working_day_without_intervals_is_handled_gracefully(rule: DureeTravailRule, ctx):
    """
    Cas de robustesse: jour WORKING mais intervals vides (donnée invalide ou jour particulier).
    Avec le fix start_dt/end_dt safe, ça ne doit pas 500.
    Ici, worked_minutes = 0 => devrait déclencher violation min.
    """
    d = date(2026, 2, 10)

    day = RhDay(
        agent_id=1,
        day_date=d,
        day_type=DayType.WORKING,
        intervals=[],
        forfait_minutes=None,
    )

    result = rule.check_day(ctx, day)

    assert result.is_valid is False
    assert len(result.violations) == 1
    assert result.violations[0].code == "DUREE_TRAVAIL_MIN_INSUFFISANTE"

    # Important: ne doit pas planter et meta doit contenir start/end à None
    meta = result.violations[0].meta or {}
    assert meta.get("start_dt") is None
    assert meta.get("end_dt") is None
