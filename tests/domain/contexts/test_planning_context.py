# tests/domain/contexts/test_planning_context.py
from datetime import date, time

from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour


# -----------------------------------------------------------
# TEST from_planning()
# -----------------------------------------------------------

def test_from_planning(make_agent, make_workday, make_planning_like):
    d = date(2025, 1, 1)
    agent = make_agent()
    wds = [make_workday(jour=d)]

    planning_like = make_planning_like(agent, wds, d)

    ctx = PlanningContext.from_planning(planning_like)  # type: ignore[arg-type]

    assert ctx.agent is agent
    assert ctx.work_days == wds
    assert ctx.date_reference == d


# -----------------------------------------------------------
# start_date / end_date
# -----------------------------------------------------------

def test_start_end_date_empty(make_agent):
    ctx = PlanningContext(make_agent(), [])
    assert ctx.start_date is None
    assert ctx.end_date is None


def test_start_end_date_ok(make_agent, make_workday):
    w1 = make_workday(jour=date(2025, 1, 3))
    w2 = make_workday(jour=date(2025, 1, 1))
    w3 = make_workday(jour=date(2025, 1, 7))
    ctx = PlanningContext(make_agent(), [w1, w2, w3])

    assert ctx.start_date == date(2025, 1, 1)
    assert ctx.end_date == date(2025, 1, 7)


# -----------------------------------------------------------
# get_work_day
# -----------------------------------------------------------

def test_get_work_day_found(make_agent, make_workday):
    d = date(2025, 1, 3)
    w = make_workday(jour=d)
    ctx = PlanningContext(make_agent(), [w])

    assert ctx.get_work_day(d) == w


def test_get_work_day_not_found(make_agent):
    ctx = PlanningContext(make_agent(), [])
    assert ctx.get_work_day(date(2025, 1, 5)) is None


# -----------------------------------------------------------
# previous / next working day
# -----------------------------------------------------------

def test_previous_working_day_none(make_agent):
    ctx = PlanningContext(make_agent(), [])
    assert ctx.get_previous_working_day(date(2025, 1, 5)) is None


def test_next_working_day_none(make_agent):
    ctx = PlanningContext(make_agent(), [])
    assert ctx.get_next_working_day(date(2025, 1, 5)) is None


def test_previous_working_day_ok(make_agent, make_workday):
    w1 = make_workday(jour=date(2025, 1, 1))
    w2 = make_workday(jour=date(2025, 1, 3))  # previous
    w3 = make_workday(jour=date(2025, 1, 5))
    ctx = PlanningContext(make_agent(), [w1, w2, w3])

    assert ctx.get_previous_working_day(date(2025, 1, 4)) == w2


def test_next_working_day_ok(make_agent, make_workday):
    w1 = make_workday(jour=date(2025, 1, 1))
    w2 = make_workday(jour=date(2025, 1, 3))
    w3 = make_workday(jour=date(2025, 1, 5))  # next
    ctx = PlanningContext(make_agent(), [w1, w2, w3])

    assert ctx.get_next_working_day(date(2025, 1, 4)) == w3


# -----------------------------------------------------------
# GAPs
# -----------------------------------------------------------

def test_last_working_gap(make_agent, make_workday):
    w = make_workday(jour=date(2025, 1, 1))
    ctx = PlanningContext(make_agent(), [w])
    assert ctx.get_last_working_day_gap(date(2025, 1, 4)) == 3


def test_last_working_gap_none(make_agent):
    ctx = PlanningContext(make_agent(), [])
    assert ctx.get_last_working_day_gap(date(2025, 1, 4)) is None


def test_next_working_gap(make_agent, make_workday):
    w = make_workday(jour=date(2025, 1, 10))
    ctx = PlanningContext(make_agent(), [w])
    assert ctx.get_next_working_day_gap(date(2025, 1, 4)) == 6


def test_next_working_gap_none(make_agent):
    ctx = PlanningContext(make_agent(), [])
    assert ctx.get_next_working_day_gap(date(2025, 1, 4)) is None


# -----------------------------------------------------------
# repos_minutes_since_last_work_day
# -----------------------------------------------------------

def test_repos_minutes_no_prev(make_agent, make_workday):
    cur = make_workday(jour=date(2025, 1, 5))
    ctx = PlanningContext(make_agent(), [cur])
    assert ctx.get_repos_minutes_since_last_work_day(date(2025, 1, 5)) is None


def test_repos_minutes_no_times(make_agent, make_workday):
    prev = make_workday(date(2025, 1, 1), type_label="repos")
    cur = make_workday(date(2025, 1, 5))
    ctx = PlanningContext(make_agent(), [prev, cur])
    assert ctx.get_repos_minutes_since_last_work_day(date(2025, 1, 5)) is None


def test_repos_minutes_normal_day(make_agent, make_workday):
    prev = make_workday(
        jour=date(2025, 1, 1)
    )
    cur = make_workday(
        jour=date(2025, 1, 2),
    )
    ctx = PlanningContext(make_agent(), [prev, cur])

    # 01/01 10:00 → 02/01 8:00 = 26h = 1560 min
    assert ctx.get_repos_minutes_since_last_work_day(date(2025, 1, 2)) == 1320


def test_repos_minutes_midnight_wrap(make_agent, make_workday):
    # 22:00 → 06:00 next day
    prev = make_workday(
        jour=date(2025, 1, 1),
        nocturne=True
    )
    cur = make_workday(
        jour=date(2025, 1, 2),
    )
    ctx = PlanningContext(make_agent(), [prev, cur])

    # end_prev = 02/01 06:00 ; start_curr = 02/01 08:00 → 2h = 120
    assert ctx.get_repos_minutes_since_last_work_day(date(2025, 1, 2)) == 120


# -----------------------------------------------------------
# amplitude + total hours
# -----------------------------------------------------------

def test_amplitude_for_day(make_agent, make_workday):
    w = make_workday(jour=date(2025, 1, 1))
    ctx = PlanningContext(make_agent(), [w])
    assert ctx.get_amplitude_for_day(date(2025, 1, 1)) == 120


def test_total_hours_for_period(make_agent, make_workday):
    w1 = make_workday(jour=date(2025, 1, 1))   # 2h
    w2 = make_workday(jour=date(2025, 1, 2), nocturne=True)  # 8h
    w3 = make_workday(jour=date(2025, 1, 3), type_label="repos")  # 0h
    ctx = PlanningContext(make_agent(), [w1, w2, w3])

    assert ctx.get_total_hours_for_period() == 10


# -----------------------------------------------------------
# GPT segments
# -----------------------------------------------------------

def test_gpt_no_work(make_agent, make_workday):
    d1 = make_workday(date(2025, 1, 1), type_label="repos")
    ctx = PlanningContext(make_agent(), [d1])
    assert ctx.get_gpt_segments() == []


def test_gpt_single_segment(make_agent, make_workday):
    w1 = make_workday(date(2025, 1, 1))
    w2 = make_workday(date(2025, 1, 2))
    ctx = PlanningContext(make_agent(), [w1, w2])

    result = ctx.get_gpt_segments()
    assert len(result) == 1
    assert result[0] == [w1, w2]


def test_gpt_multiple_segments(make_agent, make_workday):
    w1 = make_workday(date(2025, 1, 1))
    w2 = make_workday(date(2025, 1, 2))
    r = make_workday(date(2025, 1, 3), type_label="repos")
    w3 = make_workday(date(2025, 1, 4))
    ctx = PlanningContext(make_agent(), [w1, w2, r, w3])

    result = ctx.get_gpt_segments()
    assert len(result) == 2
    assert result[0] == [w1, w2]
    assert result[1] == [w3]