from datetime import date, timedelta

import pytest

from core.application.services.planning.periode_conges_analyzer import PeriodeCongesAnalyzer
from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities import TypeJour


# -----------------------------
# Cas simples
# -----------------------------


def test_detect_empty_context_returns_empty_list(make_agent):
    analyzer = PeriodeCongesAnalyzer()
    ctx = PlanningContext(
        agent=make_agent(),
        work_days=[],
        date_reference=date(2024, 1, 1),
    )

    periodes = analyzer.detect(ctx)

    assert periodes == []


def test_detect_only_working_days_returns_empty_list(make_agent, make_workday):
    analyzer = PeriodeCongesAnalyzer()
    d0 = date(2024, 1, 1)

    # 5 jours de POSTE consécutifs
    days = [
        make_workday(jour=d0 + timedelta(days=i), type_label="poste")
        for i in range(5)
    ]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=days,
        date_reference=d0,
    )

    periodes = analyzer.detect(ctx)

    assert periodes == []


def test_single_conge_is_one_periode(make_agent, make_workday):
    analyzer = PeriodeCongesAnalyzer()
    d = date(2024, 2, 10)

    work_days = [
        make_workday(jour=d - timedelta(days=1), type_label="poste"),
        make_workday(jour=d, type_label="conge"),
        make_workday(jour=d + timedelta(days=1), type_label="poste"),
    ]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=work_days,
        date_reference=d - timedelta(days=1),
    )

    periodes = analyzer.detect(ctx)

    assert len(periodes) == 1
    p = periodes[0]
    assert p.start == d
    assert p.end == d
    assert p.nb_jours == 1
    assert p.nb_conges == 1


# -----------------------------
# Blocs consécutifs CONGE/REPOS
# -----------------------------


def test_conge_plus_repos_in_one_block(make_agent, make_workday):
    """
    CONGE + REPOS consécutifs => une seule période
    avec nb_jours = 2 et nb_conges = 1.
    """
    analyzer = PeriodeCongesAnalyzer()
    d0 = date(2024, 3, 1)

    wd_conge = make_workday(jour=d0, type_label="conge")
    wd_repos = make_workday(jour=d0 + timedelta(days=1), type_label="repos")

    # On mélange l'ordre pour vérifier le tri interne
    work_days = [wd_repos, wd_conge]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=work_days,
        date_reference=d0,
    )

    periodes = analyzer.detect(ctx)

    assert len(periodes) == 1
    p = periodes[0]
    assert p.start == d0
    assert p.end == d0 + timedelta(days=1)
    assert p.nb_jours == 2
    assert p.nb_conges == 1


def test_multiple_conges_and_repos_in_block(make_agent, make_workday):
    """
    CONGE - CONGE - REPOS - REPOS -> une seule période
    nb_jours = 4, nb_conges = 2
    """
    analyzer = PeriodeCongesAnalyzer()
    d0 = date(2024, 4, 1)

    work_days = [
        make_workday(jour=d0 + timedelta(days=0), type_label="conge"),
        make_workday(jour=d0 + timedelta(days=1), type_label="conge"),
        make_workday(jour=d0 + timedelta(days=2), type_label="repos"),
        make_workday(jour=d0 + timedelta(days=3), type_label="repos"),
    ]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=work_days,
        date_reference=d0,
    )

    periodes = analyzer.detect(ctx)

    assert len(periodes) == 1
    p = periodes[0]
    assert p.start == d0
    assert p.end == d0 + timedelta(days=3)
    assert p.nb_jours == 4
    assert p.nb_conges == 2


# -----------------------------
# Découpage en plusieurs périodes
# -----------------------------


def test_conge_blocks_separated_by_work_days(make_agent, make_workday):
    """
    CONGE, REPOS, POSTE, CONGE, REPOS =>
    2 périodes distinctes.
    """
    analyzer = PeriodeCongesAnalyzer()
    d0 = date(2024, 5, 1)

    work_days = [
        make_workday(jour=d0, type_label="conge"),
        make_workday(jour=d0 + timedelta(days=1), type_label="repos"),
        make_workday(jour=d0 + timedelta(days=2), type_label="poste"),   # coupe le bloc
        make_workday(jour=d0 + timedelta(days=3), type_label="conge"),
        make_workday(jour=d0 + timedelta(days=4), type_label="repos"),
    ]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=work_days,
        date_reference=d0,
    )

    periodes = analyzer.detect(ctx)

    assert len(periodes) == 2

    p1, p2 = periodes

    assert p1.start == d0
    assert p1.end == d0 + timedelta(days=1)
    assert p1.nb_conges == 1

    assert p2.start == d0 + timedelta(days=3)
    assert p2.end == d0 + timedelta(days=4)
    assert p2.nb_conges == 1


def test_non_consecutive_conge_and_repos(make_agent, make_workday):
    """
    CONGE (jour1), REPOS (jour3) -> non consécutifs.

    Nouvelle logique :
    - le bloc [jour1] (CONGE) donne 1 période
    - le bloc [jour3] (REPOS seul) est ignoré
    """
    analyzer = PeriodeCongesAnalyzer()
    d0 = date(2024, 6, 1)

    wd_conge = make_workday(jour=d0, type_label="conge")
    wd_repos = make_workday(jour=d0 + timedelta(days=2), type_label="repos")

    work_days = [wd_conge, wd_repos]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=work_days,
        date_reference=d0,
    )

    periodes = analyzer.detect(ctx)

    assert len(periodes) == 1
    p = periodes[0]
    assert p.start == d0
    assert p.end == d0
    assert p.nb_jours == 1
    assert p.nb_conges == 1


# -----------------------------
# Blocs de repos sans congé
# -----------------------------


def test_pure_repos_blocks_are_ignored(make_agent, make_workday):
    """
    Bloc uniquement REPOS sans CONGE -> ignoré.
    """
    analyzer = PeriodeCongesAnalyzer()
    d0 = date(2024, 7, 1)

    work_days = [
        make_workday(jour=d0 + timedelta(days=i), type_label="repos")
        for i in range(3)
    ]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=work_days,
        date_reference=d0,
    )

    periodes = analyzer.detect(ctx)

    # On ne veut pas de période "congés" sans congés
    assert periodes == []


# -----------------------------
# Ordre des work_days
# -----------------------------


def test_analyzer_is_order_independent(make_agent, make_workday):
    """
    Les work_days peuvent être fournis dans n'importe quel ordre :
    l'analyzer doit trier par date en interne.
    """
    analyzer = PeriodeCongesAnalyzer()
    d0 = date(2024, 8, 1)

    wds = [
        make_workday(jour=d0 + timedelta(days=2), type_label="repos"),
        make_workday(jour=d0, type_label="conge"),
        make_workday(jour=d0 + timedelta(days=1), type_label="repos"),
    ]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=wds,
        date_reference=d0,
    )

    periodes = analyzer.detect(ctx)

    assert len(periodes) == 1
    p = periodes[0]
    assert p.start == d0
    assert p.end == d0 + timedelta(days=2)
    assert p.nb_conges == 1


# -----------------------------
# API générique detect_from_workdays
# -----------------------------


def test_detect_from_workdays_matches_detect(make_agent, make_workday):
    """
    Vérifie que detect_from_workdays et detect(PlanningContext)
    produisent le même résultat sur un échantillon simple.
    """
    analyzer = PeriodeCongesAnalyzer()
    d0 = date(2024, 9, 1)

    work_days = [
        make_workday(jour=d0, type_label="conge"),
        make_workday(jour=d0 + timedelta(days=1), type_label="repos"),
        make_workday(jour=d0 + timedelta(days=2), type_label="poste"),
    ]

    ctx = PlanningContext(
        agent=make_agent(),
        work_days=work_days,
        date_reference=d0,
    )

    periodes_ctx = analyzer.detect(ctx)
    periodes_raw = analyzer.detect_from_workdays(work_days)

    assert len(periodes_ctx) == len(periodes_raw)
    assert [(p.start, p.end, p.nb_conges) for p in periodes_ctx] == [
        (p.start, p.end, p.nb_conges) for p in periodes_raw
    ]
