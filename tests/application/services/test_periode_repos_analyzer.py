from datetime import date

import pytest

from core.application.services.planning.periode_repos_analyzer import PeriodeReposAnalyzer
from core.domain.contexts.planning_context import PlanningContext


# =====================================================================
#                              TESTS
# =====================================================================


def test_no_workdays_returns_empty_list(make_agent):
    analyzer = PeriodeReposAnalyzer()
    context = PlanningContext(
        agent=make_agent(),
        work_days=[],
    )

    assert analyzer.detect(context) == []


def test_no_repos_detects_none(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 1, 1), type_label="poste"),
        make_workday(jour=date(2024, 1, 2), type_label="poste"),
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert periods == []


def test_single_repos_detected(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 1, 1), type_label="poste"),
        make_workday(jour=date(2024, 1, 2), type_label="repos"),
        make_workday(jour=date(2024, 1, 3), type_label="poste"),
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert len(periods) == 1
    p = periods[0]
    assert p.nb_jours == 1
    assert p.start == date(2024, 1, 2)
    assert p.end == date(2024, 1, 2)


def test_double_repos_detected(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 1, 1), type_label="repos"),
        make_workday(jour=date(2024, 1, 2), type_label="repos"),
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert len(periods) == 1
    p = periods[0]
    assert p.nb_jours == 2
    assert p.start == date(2024, 1, 1)
    assert p.end == date(2024, 1, 2)


def test_triple_repos_detected(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 2, 1), type_label="repos"),
        make_workday(jour=date(2024, 2, 2), type_label="repos"),
        make_workday(jour=date(2024, 2, 3), type_label="repos"),
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert len(periods) == 1
    assert periods[0].nb_jours == 3
    assert periods[0].start == date(2024, 2, 1)
    assert periods[0].end == date(2024, 2, 3)


def test_two_separate_repos_blocks(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 3, 1), type_label="repos"),
        make_workday(jour=date(2024, 3, 2), type_label="poste"),
        make_workday(jour=date(2024, 3, 3), type_label="repos"),
        make_workday(jour=date(2024, 3, 4), type_label="repos"),
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert len(periods) == 2

    p1, p2 = periods

    assert p1.nb_jours == 1
    assert p1.start == date(2024, 3, 1)
    assert p1.end == date(2024, 3, 1)

    assert p2.nb_jours == 2
    assert p2.start == date(2024, 3, 3)
    assert p2.end == date(2024, 3, 4)


def test_repos_block_at_start_and_end(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 4, 1), type_label="repos"),
        make_workday(jour=date(2024, 4, 2), type_label="poste"),
        make_workday(jour=date(2024, 4, 3), type_label="poste"),
        make_workday(jour=date(2024, 4, 4), type_label="repos"),
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert len(periods) == 2
    assert periods[0].start == date(2024, 4, 1)
    assert periods[0].end == date(2024, 4, 1)
    assert periods[1].start == date(2024, 4, 4)
    assert periods[1].end == date(2024, 4, 4)


def test_detect_works_with_unordered_workdays(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 5, 2), type_label="repos"),
        make_workday(jour=date(2024, 5, 1), type_label="repos"),  # inverse order
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert len(periods) == 1
    p = periods[0]
    assert p.start == date(2024, 5, 1)
    assert p.end == date(2024, 5, 2)
    assert p.nb_jours == 2


def test_single_workday_repos(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 6, 1), type_label="repos"),
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert len(periods) == 1
    p = periods[0]
    assert p.nb_jours == 1
    assert p.start == date(2024, 6, 1)
    assert p.end == date(2024, 6, 1)


def test_mixed_types_in_complex_scenario(make_agent, make_workday):
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 7, 1), type_label="poste"),
        make_workday(jour=date(2024, 7, 2), type_label="repos"),
        make_workday(jour=date(2024, 7, 3), type_label="repos"),
        make_workday(jour=date(2024, 7, 4), type_label="absence"),  # break
        make_workday(jour=date(2024, 7, 5), type_label="repos"),
    ]

    periods = analyzer.detect(
        PlanningContext(agent=make_agent(), work_days=days)
    )

    assert len(periods) == 2
    p1, p2 = periods

    assert p1.nb_jours == 2   # 2–3
    assert p1.start == date(2024, 7, 2)
    assert p1.end == date(2024, 7, 3)

    assert p2.nb_jours == 1   # 5
    assert p2.start == date(2024, 7, 5)
    assert p2.end == date(2024, 7, 5)


# ---------------------------------------------------------------------
# API générique detect_from_workdays
# ---------------------------------------------------------------------


def test_detect_from_workdays_matches_detect(make_agent, make_workday):
    """
    Vérifie que detect_from_workdays et detect(PlanningContext)
    produisent le même résultat.
    """
    analyzer = PeriodeReposAnalyzer()
    days = [
        make_workday(jour=date(2024, 8, 1), type_label="repos"),
        make_workday(jour=date(2024, 8, 2), type_label="repos"),
        make_workday(jour=date(2024, 8, 3), type_label="poste"),
    ]

    ctx = PlanningContext(agent=make_agent(), work_days=days)

    periods_ctx = analyzer.detect(ctx)
    periods_raw = analyzer.detect_from_workdays(days)

    assert len(periods_ctx) == len(periods_raw)
    assert [(p.start, p.end, p.nb_jours) for p in periods_ctx] == [
        (p.start, p.end, p.nb_jours) for p in periods_raw
    ]
