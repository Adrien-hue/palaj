from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from typing import cast

from core.domain.enums.day_type import DayType
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_interval import RhInterval
from core.rh_rules.general.rule_repos_double import ReposDoubleRule


pytestmark = [pytest.mark.unit, pytest.mark.rh]


@dataclass(frozen=True)
class _FakeGpt:
    start: date
    end: date
    nb_jours: int
    is_left_truncated: bool = False
    is_right_truncated: bool = False


class _FakeAnalyzer:
    def __init__(self, gpts: list[_FakeGpt]):
        self._gpts = gpts

    def detect_from_rh_days(self, *args, **kwargs):
        return self._gpts


def _rh_day(d: date, day_type: DayType) -> RhDay:
    return RhDay(
        agent_id=1,
        day_date=d,
        day_type=day_type,
        intervals=[],
        forfait_minutes=None,
    )


def _ctx(days: list[RhDay], start: date | None, end: date | None) -> SimpleNamespace:
    by_date = {d.day_date: d for d in days}
    return SimpleNamespace(
        days=days,
        by_date=by_date,
        effective_start=start,
        effective_end=end,
    )


def test_ok_when_no_days():
    rule = ReposDoubleRule(analyzer=_FakeAnalyzer([]))
    ctx = _ctx(days=[], start=date(2026, 2, 1), end=date(2026, 2, 28))

    res = rule.check(cast(RhContext, ctx))
    assert res.is_valid is True
    assert res.violations == []


def test_error_when_dates_missing():
    rule = ReposDoubleRule(analyzer=_FakeAnalyzer([]))
    ctx = _ctx(days=[_rh_day(date(2026, 2, 10), DayType.WORKING)], start=None, end=None)

    res = rule.check(cast(RhContext, ctx))

    assert res.is_valid is False
    assert len(res.violations) == 1
    assert res.violations[0].code == "REPOS_DOUBLE_DATES_MISSING"


def test_ignore_left_truncated_gpt():
    gpt = _FakeGpt(start=date(2026, 2, 3), end=date(2026, 2, 8), nb_jours=6, is_left_truncated=True)
    rule = ReposDoubleRule(analyzer=_FakeAnalyzer([gpt]))
    ctx = _ctx(days=[_rh_day(date(2026, 2, 1), DayType.WORKING)], start=date(2026, 2, 1), end=date(2026, 2, 28))

    res = rule.check(cast(RhContext, ctx))
    assert res.is_valid is True
    assert res.violations == []


def test_ignore_gpt_shorter_than_6_days():
    gpt = _FakeGpt(start=date(2026, 2, 3), end=date(2026, 2, 7), nb_jours=5)
    rule = ReposDoubleRule(analyzer=_FakeAnalyzer([gpt]))
    ctx = _ctx(days=[_rh_day(date(2026, 2, 1), DayType.WORKING)], start=date(2026, 2, 1), end=date(2026, 2, 28))

    res = rule.check(cast(RhContext, ctx))
    assert res.is_valid is True
    assert res.violations == []


def test_violation_for_exact_6_days_without_double_rest():
    gpt = _FakeGpt(start=date(2026, 2, 3), end=date(2026, 2, 8), nb_jours=6)
    rule = ReposDoubleRule(analyzer=_FakeAnalyzer([gpt]))

    start = date(2026, 2, 1)
    end = date(2026, 2, 28)
    days = [
        _rh_day(gpt.end + timedelta(days=1), DayType.REST),
        _rh_day(gpt.end + timedelta(days=2), DayType.WORKING),
    ]
    ctx = _ctx(days=days, start=start, end=end)

    res = rule.check(cast(RhContext, ctx))
    assert res.is_valid is False
    assert len(res.violations) == 1
    assert res.violations[0].code == "REPOS_DOUBLE_MANQUANT"
    assert res.violations[0].start_date == gpt.start
    assert res.violations[0].end_date == gpt.end + timedelta(days=2)


def test_violation_for_more_than_6_days_without_double_rest():
    # Cas clé rendu possible par ton changement (>= 6)
    gpt = _FakeGpt(start=date(2026, 2, 1), end=date(2026, 2, 7), nb_jours=7)
    rule = ReposDoubleRule(analyzer=_FakeAnalyzer([gpt]))

    start = date(2026, 2, 1)
    end = date(2026, 2, 28)
    days = [
        _rh_day(gpt.end + timedelta(days=1), DayType.WORKING),
        _rh_day(gpt.end + timedelta(days=2), DayType.REST),
    ]
    ctx = _ctx(days=days, start=start, end=end)

    res = rule.check(cast(RhContext, ctx))
    assert res.is_valid is False
    assert len(res.violations) == 1
    assert res.violations[0].code == "REPOS_DOUBLE_MANQUANT"


def test_ok_for_gpt_ge_6_days_with_two_consecutive_rest_days():
    gpt = _FakeGpt(start=date(2026, 2, 3), end=date(2026, 2, 8), nb_jours=6)
    rule = ReposDoubleRule(analyzer=_FakeAnalyzer([gpt]))

    start = date(2026, 2, 1)
    end = date(2026, 2, 28)
    days = [
        _rh_day(gpt.end + timedelta(days=1), DayType.REST),
        _rh_day(gpt.end + timedelta(days=2), DayType.REST),
    ]
    ctx = _ctx(days=days, start=start, end=end)

    res = rule.check(cast(RhContext, ctx))
    assert res.is_valid is True
    assert res.violations == []


def test_ignore_when_window_does_not_include_needed_days_after_gpt_end():
    gpt = _FakeGpt(start=date(2026, 2, 3), end=date(2026, 2, 8), nb_jours=6)
    rule = ReposDoubleRule(analyzer=_FakeAnalyzer([gpt]))

    # Fenêtre trop courte: end == gpt.end + 1, or la règle veut gpt.end + 2
    start = date(2026, 2, 1)
    end = gpt.end + timedelta(days=1)
    days = [
        _rh_day(gpt.end + timedelta(days=1), DayType.REST),
    ]
    ctx = _ctx(days=days, start=start, end=end)

    res = rule.check(cast(RhContext, ctx))
    assert res.is_valid is True
    assert res.violations == []
