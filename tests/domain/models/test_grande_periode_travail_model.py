from datetime import date

import pytest

from core.domain.models.work_day import WorkDay
from core.domain.models.grande_periode_travail import GrandePeriodeTravail

def test_grande_periode_travail_computed_properties(make_workday):
    days = [make_workday(jour=date(2024, 1, i)) for i in range(1, 4)]
    gpt = GrandePeriodeTravail.from_workdays(days)

    assert gpt is not None
    assert gpt.start == date(2024, 1, 1)
    assert gpt.end == date(2024, 1, 3)
    assert gpt.nb_jours == 3
    assert gpt.total_minutes == sum(wd.duree_minutes() for wd in days)
    assert gpt.has_poste is True
    assert gpt.category() == "Travail"
    assert "GPT 2024-01-01 → 2024-01-03" in str(gpt)


def test_grande_periode_travail_detects_mixed_and_absence_only(make_workday):
    work = make_workday(jour=date(2024, 2, 1), type_label="poste")
    absence = make_workday(jour=date(2024, 2, 2), type_label="absence")
    conge = make_workday(jour=date(2024, 2, 3), type_label="conge")

    mixed = GrandePeriodeTravail.from_workdays([work, absence])
    absence_only = GrandePeriodeTravail.from_workdays([absence, conge])

    assert mixed is not None
    assert mixed.category() == "Mixte"
    assert mixed.is_mixed()
    assert absence_only is not None
    assert absence_only.category() == "Absence / Congé"
    assert absence_only.is_absence_only()


def test_grande_periode_travail_truncation_flags_and_maximum(make_workday):
    days = [make_workday(jour=date(2024, 3, i)) for i in range(1, 7)]
    gpt = GrandePeriodeTravail.from_workdays(days, is_left_truncated=True)

    assert gpt is not None
    assert gpt.is_left_truncated is True
    assert gpt.is_truncated is True
    assert gpt.is_complete is False
    assert gpt.is_maximum() is True


def test_grande_periode_travail_requires_consecutive_days(make_workday):
    d1 = make_workday(jour=date(2024, 4, 1))
    d2 = make_workday(jour=date(2024, 4, 3))

    with pytest.raises(ValueError):
        GrandePeriodeTravail.from_workdays([d1, d2])


def test_grande_periode_travail_empty_list_returns_none(make_workday):
    assert GrandePeriodeTravail.from_workdays([]) is None

def test_category_absence_only(make_workday):
    days = [
        make_workday(jour=date(2025,1,1), type_label="absence"),
        make_workday(jour=date(2025,1,2), type_label="conge"),
    ]
    gpt = GrandePeriodeTravail.from_workdays(days)
    assert gpt is not None
    assert gpt.category() == "Absence / Congé"

def test_category_work_only(make_workday):
    days = [
        make_workday(jour=date(2025,1,1), type_label="poste"),
        make_workday(jour=date(2025,1,2), type_label="zcot"),
    ]
    gpt = GrandePeriodeTravail.from_workdays(days)
    assert gpt is not None
    assert gpt.category() == "Travail"

def test_category_mixte(make_workday):
    days = [
        make_workday(jour=date(2025,1,1), type_label="poste"),
        make_workday(jour=date(2025,1,2), type_label="conge"),
    ]
    gpt = GrandePeriodeTravail.from_workdays(days)
    assert gpt is not None
    assert gpt.category() == "Mixte"

def test_truncated_left(make_workday):
    gpt = GrandePeriodeTravail([make_workday(jour=date.today(), type_label="poste")], is_left_truncated=True)
    assert gpt.is_truncated is True
    assert gpt.is_complete is False

def test_truncated_right(make_workday):
    gpt = GrandePeriodeTravail([make_workday(jour=date.today(), type_label="poste")], is_right_truncated=True)
    assert gpt.is_truncated is True
    assert gpt.is_complete is False


def test_not_truncated(make_workday):
    gpt = GrandePeriodeTravail([make_workday(jour=date.today(), type_label="poste")])
    assert gpt.is_truncated is False
    assert gpt.is_complete is True

def test_has_nocturne(make_workday):
    gpt = GrandePeriodeTravail([make_workday(jour=date.today(), type_label="poste", nocturne=True)])
    assert gpt.has_nocturne is True

def test_category_empty(make_workday):
    gpt = GrandePeriodeTravail([make_workday(jour=date.today(), type_label="inconnu")])
    assert gpt.category() == "Vide"

def test_contient(make_workday):
    gpt = GrandePeriodeTravail([make_workday(jour=date(2025,1,1), type_label="poste")])
    assert gpt.contient(date(2025,1,1)) is True
    assert gpt.contient(date(2025,1,2)) is False
    

def test_str_output(make_workday):
    days = [
        make_workday(jour=date(2025,1,1), type_label="poste"), # 2h
        make_workday(jour=date(2025,1,2), type_label="zcot"), # 7h
        make_workday(jour=date(2025,1,3), type_label="absence"),
        make_workday(jour=date(2025,1,4), type_label="conge"),
    ]
    gpt = GrandePeriodeTravail.from_workdays(days)
    txt = str(gpt)

    assert "GPT 2025-01-01 → 2025-01-04" in txt
    assert "9h" in txt
    assert "Poste" in txt
    assert "ZCOT" in txt
    assert "Absence" in txt
    assert "Congé" in txt

def test_from_workdays_not_consecutive(make_workday):
    d1 = make_workday(jour=date(2025,1,1), type_label="poste")
    d3 = make_workday(jour=date(2025,1,3), type_label="poste")
    with pytest.raises(ValueError):
        GrandePeriodeTravail.from_workdays([d1, d3])