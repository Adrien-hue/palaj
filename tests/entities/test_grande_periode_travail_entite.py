import pytest
from datetime import date, timedelta
from core.domain.entities.grande_periode_travail import GrandePeriodeTravail
from core.domain.entities.work_day import WorkDay
from core.domain.entities.etat_jour_agent import EtatJourAgent, TypeJour
from core.domain.entities.tranche import Tranche


# -------------------------------------------------------------------
# 🔧 Helpers
# -------------------------------------------------------------------

def make_workday(jour: date, type_jour: TypeJour, has_tranche=True) -> WorkDay:
    etat = EtatJourAgent(agent_id=1, jour=jour, type_jour=type_jour)
    tranches = [Tranche(1, "MJ", "08:00", "16:00")] if has_tranche else []
    return WorkDay(jour=jour, etat=etat, tranches=tranches)


def make_gpt(nb_days=3, start_date=date(2025, 1, 1), type_jour=TypeJour.POSTE, **kwargs):
    days = [make_workday(start_date + timedelta(days=i), type_jour) for i in range(nb_days)]
    return GrandePeriodeTravail.from_workdays(days, **kwargs)


# -------------------------------------------------------------------
# 1️⃣ Construction et cohérence de base
# -------------------------------------------------------------------

def test_from_workdays_valid_sequence():
    days = [make_workday(date(2025, 1, d), TypeJour.POSTE) for d in (1, 2, 3)]
    gpt = GrandePeriodeTravail.from_workdays(days)
    assert gpt.nb_jours == 3
    assert gpt.start == date(2025, 1, 1)
    assert gpt.end == date(2025, 1, 3)
    assert gpt.total_minutes > 0
    assert not gpt.is_truncated
    assert gpt.is_complete


def test_from_workdays_non_consecutive_raises():
    days = [make_workday(date(2025, 1, 1), TypeJour.POSTE),
            make_workday(date(2025, 1, 3), TypeJour.POSTE)]
    with pytest.raises(ValueError):
        GrandePeriodeTravail.from_workdays(days)


def test_from_workdays_empty_returns_none():
    assert GrandePeriodeTravail.from_workdays([]) is None


# -------------------------------------------------------------------
# 2️⃣ Calculs et propriétés
# -------------------------------------------------------------------

def test_properties_work_and_absence_flags():
    days = [
        make_workday(date(2025, 1, 1), TypeJour.POSTE),
        make_workday(date(2025, 1, 2), TypeJour.ZCOT),
        make_workday(date(2025, 1, 3), TypeJour.ABSENCE),
        make_workday(date(2025, 1, 4), TypeJour.CONGE),
    ]
    gpt = GrandePeriodeTravail.from_workdays(days)
    assert gpt.has_poste
    assert gpt.has_zcot
    assert gpt.has_absence
    assert gpt.has_conge
    assert gpt.has_nocturne is False  # nos tranches sont diurnes


def test_is_maximum_and_contient():
    gpt = make_gpt(nb_days=6)
    assert gpt.is_maximum()
    assert gpt.contient(gpt.start)
    assert gpt.contient(gpt.end)
    assert not gpt.contient(gpt.end + timedelta(days=1))


def test_total_minutes_sums_correctly():
    gpt = make_gpt(nb_days=2)
    expected = sum(wd.duree_minutes() for wd in gpt.workdays)
    assert gpt.total_minutes == expected


# -------------------------------------------------------------------
# 3️⃣ Catégorisation logique
# -------------------------------------------------------------------

def test_is_absence_only():
    gpt = make_gpt(nb_days=3, type_jour=TypeJour.ABSENCE)
    assert gpt.is_absence_only()
    assert gpt.category() == "Absence / Congé"


def test_is_work_only():
    gpt = make_gpt(nb_days=3, type_jour=TypeJour.ZCOT)
    assert gpt.is_work_only()
    assert gpt.category() == "Travail"


def test_is_mixed_combines_work_and_absence():
    days = [
        make_workday(date(2025, 1, 1), TypeJour.POSTE),
        make_workday(date(2025, 1, 2), TypeJour.ABSENCE),
    ]
    gpt = GrandePeriodeTravail.from_workdays(days)
    assert gpt.is_mixed()
    assert gpt.category() == "Mixte"


def test_is_empty_case():
    # Aucun jour significatif
    day = make_workday(date(2025, 1, 1), TypeJour.REPOS)
    gpt = GrandePeriodeTravail.from_workdays([day])
    assert gpt.is_empty()
    assert gpt.category() == "Vide"


# -------------------------------------------------------------------
# 4️⃣ Troncatures
# -------------------------------------------------------------------

def test_truncated_flags_behavior():
    gpt = make_gpt(nb_days=3, is_left_truncated=True)
    assert gpt.is_truncated
    assert not gpt.is_right_truncated or gpt.is_left_truncated
    assert not gpt.is_complete

    gpt2 = make_gpt(nb_days=3, is_right_truncated=True)
    assert gpt2.is_truncated


# -------------------------------------------------------------------
# 5️⃣ Affichage et __str__
# -------------------------------------------------------------------

def test_str_representation_contains_all_info():
    gpt = make_gpt(nb_days=2, type_jour=TypeJour.POSTE)
    s = str(gpt)
    assert "GPT" in s
    assert str(gpt.start) in s
    assert str(gpt.end) in s
    assert "Poste" in s
    assert "jours" in s
    assert "(" in s and ")" in s
