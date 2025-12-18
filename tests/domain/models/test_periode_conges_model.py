from datetime import date, timedelta

import pytest

from core.domain.models.periode_conges import PeriodeConges


# -----------------------------
# from_workdays : cas valides
# -----------------------------


def test_from_workdays_simple_conge(make_workday):
    """Une seule journée de congé → période valide, 1 jour / 1 congé."""
    d = date(2024, 1, 10)
    wd = make_workday(d, type_label="conge")

    periode = PeriodeConges.from_workdays([wd])

    assert periode.start == d
    assert periode.end == d
    assert periode.nb_jours == 1
    assert periode.nb_conges == 1
    assert periode.jours == [d]
    assert "1j" in periode.label()
    assert "1j de congés" in periode.label()


def test_from_workdays_conge_plus_repos(make_workday):
    """Bloc CONGE + REPOS consécutifs → période 2 jours / 1 congé."""
    d1 = date(2024, 2, 1)
    d2 = d1 + timedelta(days=1)

    wd1 = make_workday(d1, type_label="conge")
    wd2 = make_workday(d2, type_label="repos")

    # ordre inversé volontaire pour vérifier le tri
    periode = PeriodeConges.from_workdays([wd2, wd1])

    assert periode.start == d1
    assert periode.end == d2
    assert periode.nb_jours == 2
    assert periode.nb_conges == 1
    assert periode.jours == [d1, d2]


def test_from_workdays_tous_conges(make_workday):
    """3 jours de CONGE consécutifs → période 3 jours / 3 congés."""
    d0 = date(2024, 3, 1)
    days = [d0 + timedelta(days=i) for i in range(3)]
    wds = [make_workday(j, type_label="conge") for j in days]

    periode = PeriodeConges.from_workdays(wds)

    assert periode.nb_jours == 3
    assert periode.nb_conges == 3
    assert periode.start == days[0]
    assert periode.end == days[-1]


# -----------------------------
# from_workdays : cas invalides
# -----------------------------


def test_from_workdays_empty_raises():
    """Liste vide → ValueError."""
    with pytest.raises(ValueError) as exc:
        PeriodeConges.from_workdays([])
    assert "au moins un WorkDay" in str(exc.value)


def test_from_workdays_non_consecutives_raises(make_workday):
    """Jours non consécutifs → ValueError."""
    d1 = date(2024, 4, 1)
    d2 = d1 + timedelta(days=2)  # trou d'un jour

    wd1 = make_workday(d1, type_label="conge")
    wd2 = make_workday(d2, type_label="repos")

    with pytest.raises(ValueError) as exc:
        PeriodeConges.from_workdays([wd1, wd2])
    assert "non consécutifs" in str(exc.value)


def test_from_workdays_with_invalid_type_raises(make_workday):
    """Présence d’un jour non CONGE/REPOS (POSTE, ZCOT, etc.) → ValueError."""
    d1 = date(2024, 5, 1)
    d2 = d1 + timedelta(days=1)

    wd_conge = make_workday(d1, type_label="conge")
    wd_poste = make_workday(d2, type_label="poste")  # invalide pour PeriodeConges

    with pytest.raises(ValueError) as exc:
        PeriodeConges.from_workdays([wd_conge, wd_poste])

    assert "ne peut contenir que CONGE/REPOS" in str(exc.value)


def test_from_workdays_without_any_conge_raises(make_workday):
    """Bloc uniquement REPOS (sans CONGE) → ValueError."""
    d1 = date(2024, 6, 1)
    d2 = d1 + timedelta(days=1)

    wd1 = make_workday(d1, type_label="repos")
    wd2 = make_workday(d2, type_label="repos")

    with pytest.raises(ValueError) as exc:
        PeriodeConges.from_workdays([wd1, wd2])

    assert "au moins un jour CONGE" in str(exc.value)


# -----------------------------
# Représentation & label
# -----------------------------


def test_label_and_str_format(make_workday):
    """label() et __str__ doivent refléter correctement la période."""
    d0 = date(2024, 7, 1)
    days = [d0 + timedelta(days=i) for i in range(4)]  # 4 jours

    wds = [
        make_workday(days[0], type_label="conge"),
        make_workday(days[1], type_label="conge"),
        make_workday(days[2], type_label="repos"),
        make_workday(days[3], type_label="repos"),
    ]

    periode = PeriodeConges.from_workdays(wds)

    assert periode.nb_jours == 4
    assert periode.nb_conges == 2

    label = periode.label()
    s = str(periode)

    assert "4j" in label
    assert "2j de congés" in label
    assert str(periode.start) in s
    assert str(periode.end) in s
