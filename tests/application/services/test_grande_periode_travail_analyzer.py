from datetime import date, timedelta

import pytest

from core.application.services.planning.grande_periode_travail_analyzer import (
    GrandePeriodeTravailAnalyzer,
)
from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour


def _bounds(gpts):
    """Retourne une liste de (start, end) pour faciliter les assertions."""
    return [(g.start, g.end) for g in gpts]


# --------------------------------------------------------------------
# detect_from_workdays : cas simples et découpage
# --------------------------------------------------------------------


def test_detect_from_workdays_empty_list_returns_empty():
    analyzer = GrandePeriodeTravailAnalyzer()
    gpts = analyzer.detect_from_workdays([])
    assert gpts == []


def test_single_gpt_all_non_repos(make_workday):
    """
    Suite de jours non REPOS -> une seule GPT.
    POSTE / ZCOT / ABSENCE / CONGE sont tous inclus.
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 1, 1)

    work_days = [
        make_workday(jour=d0, type_label="poste"),
        make_workday(jour=d0 + timedelta(days=1), type_label="zcot"),
        make_workday(jour=d0 + timedelta(days=2), type_label="absence"),
        make_workday(jour=d0 + timedelta(days=3), type_label="conge"),
    ]

    gpts = analyzer.detect_from_workdays(work_days)

    assert len(gpts) == 1
    g = gpts[0]
    assert g.start == d0
    assert g.end == d0 + timedelta(days=3)


def test_repos_splits_gpts(make_workday):
    """
    Les jours REPOS coupent les GPT.
    Exemple :
      POSTE, POSTE, REPOS, ZCOT, CONGE, REPOS -> 2 GPT.
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 1, 10)

    work_days = [
        make_workday(jour=d0, type_label="poste"),
        make_workday(jour=d0 + timedelta(days=1), type_label="poste"),
        make_workday(jour=d0 + timedelta(days=2), type_label="repos"),
        make_workday(jour=d0 + timedelta(days=3), type_label="zcot"),
        make_workday(jour=d0 + timedelta(days=4), type_label="conge"),
        make_workday(jour=d0 + timedelta(days=5), type_label="repos"),
    ]

    gpts = analyzer.detect_from_workdays(work_days)

    assert len(gpts) == 2
    (s1, e1), (s2, e2) = _bounds(gpts)
    assert (s1, e1) == (d0, d0 + timedelta(days=1))
    assert (s2, e2) == (d0 + timedelta(days=3), d0 + timedelta(days=4))


def test_only_repos_returns_no_gpt(make_workday):
    """
    Liste composée uniquement de REPOS -> aucune GPT.
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 2, 1)

    work_days = [
        make_workday(jour=d0 + timedelta(days=i), type_label="repos")
        for i in range(4)
    ]

    gpts = analyzer.detect_from_workdays(work_days)

    assert gpts == []


def test_order_independent_detection(make_workday):
    """
    L'analyse doit être indépendante de l'ordre d'entrée des work_days.
    On mélange l'ordre, mais la GPT doit couvrir les dates min/max.
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 3, 1)

    wd1 = make_workday(jour=d0, type_label="poste")
    wd2 = make_workday(jour=d0 + timedelta(days=1), type_label="conge")
    wd3 = make_workday(jour=d0 + timedelta(days=2), type_label="absence")

    # ordre mélangé
    work_days = [wd3, wd1, wd2]

    gpts = analyzer.detect_from_workdays(work_days)

    assert len(gpts) == 1
    (start, end) = _bounds(gpts)[0]
    assert start == d0
    assert end == d0 + timedelta(days=2)


def test_trailing_non_repos_bloc_closes_gpt(make_workday):
    """
    GPT qui se termine simplement en fin de tableau (sans REPOS final)
    doit être clôturée correctement.
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 4, 1)

    work_days = [
        make_workday(jour=d0, type_label="repos"),
        make_workday(jour=d0 + timedelta(days=1), type_label="poste"),
        make_workday(jour=d0 + timedelta(days=2), type_label="zcot"),
    ]

    gpts = analyzer.detect_from_workdays(work_days)

    assert len(gpts) == 1
    (start, end) = _bounds(gpts)[0]
    assert start == d0 + timedelta(days=1)
    assert end == d0 + timedelta(days=2)


# --------------------------------------------------------------------
# Troncatures avec context_start / context_end
# --------------------------------------------------------------------


def test_gpt_truncated_on_left_boundary(make_workday):
    """
    GPT dont le début est <= context_start => is_left_truncated = True.
    Exemple :
      context_start = 5
      GPT = [4, 5, 6]
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 5, 4)

    work_days = [
        make_workday(jour=d0, type_label="poste"),                        # J4
        make_workday(jour=d0 + timedelta(days=1), type_label="poste"),    # J5
        make_workday(jour=d0 + timedelta(days=2), type_label="poste"),    # J6
    ]

    context_start = d0 + timedelta(days=1)  # J5
    context_end = d0 + timedelta(days=10)

    gpts = analyzer.detect_from_workdays(
        work_days,
        context_start=context_start,
        context_end=context_end,
    )

    assert len(gpts) == 1
    g = gpts[0]
    assert g.start == d0
    assert g.end == d0 + timedelta(days=2)
    assert g.is_left_truncated is True
    assert g.is_right_truncated is False


def test_gpt_truncated_on_right_boundary(make_workday):
    """
    GPT dont la fin est >= context_end => is_right_truncated = True.
    Exemple :
      context_end = J6
      GPT = [J4, J5, J6]
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 6, 4)

    work_days = [
        make_workday(jour=d0, type_label="poste"),                        # J4
        make_workday(jour=d0 + timedelta(days=1), type_label="poste"),    # J5
        make_workday(jour=d0 + timedelta(days=2), type_label="poste"),    # J6
    ]

    context_start = d0 - timedelta(days=10)
    context_end = d0 + timedelta(days=2)  # J6

    gpts = analyzer.detect_from_workdays(
        work_days,
        context_start=context_start,
        context_end=context_end,
    )

    assert len(gpts) == 1
    g = gpts[0]
    assert g.start == d0
    assert g.end == d0 + timedelta(days=2)
    assert g.is_left_truncated is False
    assert g.is_right_truncated is True


def test_gpt_not_truncated_when_inside_context(make_workday):
    """
    GPT strictement à l'intérieur [context_start, context_end] =>
    aucun tronquage.
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 7, 10)

    work_days = [
        make_workday(jour=d0, type_label="poste"),
        make_workday(jour=d0 + timedelta(days=1), type_label="poste"),
    ]

    context_start = d0 - timedelta(days=1)
    context_end = d0 + timedelta(days=5)

    gpts = analyzer.detect_from_workdays(
        work_days,
        context_start=context_start,
        context_end=context_end,
    )

    assert len(gpts) == 1
    g = gpts[0]
    assert g.is_left_truncated is False
    assert g.is_right_truncated is False


def test_gpt_truncated_on_both_sides(make_workday):
    """
    GPT qui déborde à gauche et à droite du contexte => 2 flags True.
    GPT = [J0..J9]
    Contexte = [J3..J6]
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    start_gpt = date(2025, 8, 1)
    work_days = [
        make_workday(jour=start_gpt + timedelta(days=i), type_label="poste")
        for i in range(10)
    ]

    context_start = start_gpt + timedelta(days=3)
    context_end = start_gpt + timedelta(days=6)

    gpts = analyzer.detect_from_workdays(
        work_days,
        context_start=context_start,
        context_end=context_end,
    )

    assert len(gpts) == 1
    g = gpts[0]
    assert g.start == start_gpt
    assert g.end == start_gpt + timedelta(days=9)
    assert g.is_left_truncated is True
    assert g.is_right_truncated is True


# --------------------------------------------------------------------
# API legacy detect(PlanningContext)
# --------------------------------------------------------------------


def test_detect_with_empty_context_returns_empty(make_agent):
    """
    detect(context) doit renvoyer [] si aucun work_day.
    """
    ctx = PlanningContext(
        agent=make_agent(),
        work_days=[],
        date_reference=date(2025, 1, 1),
    )
    analyzer = GrandePeriodeTravailAnalyzer()

    gpts = analyzer.detect(ctx)

    assert gpts == []


def test_detect_uses_context_dates_for_truncation(make_context):
    """
    Vérifie que detect(context) passe bien context_start / context_end
    aux GPT détectées.
    make_context crée par défaut :
      REPOS, (GPT...), REPOS
    """
    analyzer = GrandePeriodeTravailAnalyzer()

    start_date = date(2025, 9, 1)
    ctx = make_context(
        nb_jours=3,
        start_date=start_date,
        include_left_repos=True,
        include_right_repos=True,
    )

    # make_context :
    #   REPOS (start_date)
    #   POSTE x3
    #   REPOS (end_date)
    # context.start_date / context.end_date doivent être utilisés
    gpts = analyzer.detect(ctx)

    assert len(gpts) == 1
    g = gpts[0]

    # GPT couvre bien les 3 jours de POSTE
    assert g.start == start_date + timedelta(days=1)
    assert g.end == start_date + timedelta(days=3)

    # Comme la GPT ne commence pas avant context.start_date
    # et ne finit pas après context.end_date, elle ne doit pas
    # être marquée tronquée.
    assert g.is_left_truncated is False
    assert g.is_right_truncated is False


# --------------------------------------------------------------------
# Tests ciblés sur _finalize_gpt (bloc interne)
# --------------------------------------------------------------------


def test_finalize_gpt_with_empty_bloc_returns_none():
    analyzer = GrandePeriodeTravailAnalyzer()
    result = analyzer._finalize_gpt(
        [],
        context_start=None,
        context_end=None,
    )
    assert result is None


def test_finalize_gpt_with_bloc_and_no_context(make_workday):
    """
    _finalize_gpt sur un bloc simple sans bornes de contexte
    -> pas de tronquage.
    """
    analyzer = GrandePeriodeTravailAnalyzer()
    d0 = date(2025, 10, 1)

    bloc = [
        make_workday(jour=d0, type_label="poste"),
        make_workday(jour=d0 + timedelta(days=1), type_label="poste"),
    ]

    gpt = analyzer._finalize_gpt(
        bloc,
        context_start=None,
        context_end=None,
    )

    assert gpt is not None
    assert gpt.start == d0
    assert gpt.end == d0 + timedelta(days=1)
    assert gpt.is_left_truncated is False
    assert gpt.is_right_truncated is False
