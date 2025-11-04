import pytest
from datetime import date, time, timedelta
from core.domain.entities.work_day import WorkDay
from core.domain.entities.tranche import Tranche
from core.domain.entities.etat_jour_agent import EtatJourAgent, TypeJour
from tests.utils.text import strip_ansi


# -------------------------------------------------------------------
# 🔧 Helpers
# -------------------------------------------------------------------

def make_etat(agent_id=1, jour=date(2025, 1, 1), type_jour=TypeJour.POSTE):
    return EtatJourAgent(agent_id=agent_id, jour=jour, type_jour=type_jour)

def make_tranches():
    return [
        Tranche(1, "MJ", "06:00", "12:00"),
        Tranche(2, "AM", "13:00", "17:00"),
    ]


# -------------------------------------------------------------------
# 1️⃣ Construction et typage
# -------------------------------------------------------------------

def test_workday_creation_and_type_inference():
    e = make_etat(type_jour=TypeJour.POSTE)
    wd = WorkDay(jour=e.jour, etat=e, tranches=make_tranches())

    assert wd.jour == e.jour
    assert wd.type() == TypeJour.POSTE
    assert wd.is_working()
    assert not wd.is_rest()
    assert not wd.is_absence()
    assert isinstance(repr(wd), str)


def test_workday_type_inferred_from_tranches_when_no_etat():
    wd = WorkDay(jour=date(2025, 1, 10), etat=None, tranches=make_tranches())
    assert wd.type() == TypeJour.POSTE


def test_workday_type_inferred_as_repos_if_no_tranche():
    wd = WorkDay(jour=date(2025, 1, 10), etat=None, tranches=[])
    assert wd.type() == TypeJour.REPOS


# -------------------------------------------------------------------
# 2️⃣ Durées et amplitudes
# -------------------------------------------------------------------

def test_duree_minutes_for_poste():
    e = make_etat(type_jour=TypeJour.POSTE)
    tranches = [Tranche(1, "S1", "06:00", "14:00"), Tranche(2, "S2", "15:00", "18:00")]
    wd = WorkDay(jour=e.jour, etat=e, tranches=tranches)

    assert wd.duree_minutes() == (8 * 60 + 3 * 60)
    assert wd.duree_hours() == pytest.approx(11.0, rel=1e-2)


def test_duree_minutes_for_zcot_fixed():
    e = make_etat(type_jour=TypeJour.ZCOT)
    wd = WorkDay(jour=e.jour, etat=e, tranches=[])
    assert wd.duree_minutes() == 420
    assert wd.duree_hours() == 12.0


def test_duree_zero_for_rest_or_absence():
    for t in [TypeJour.REPOS, TypeJour.CONGE, TypeJour.ABSENCE]:
        wd = WorkDay(date(2025, 2, 1), make_etat(type_jour=t), [])
        assert wd.duree_minutes() == 0
        assert wd.duree_hours() == 0


def test_amplitude_minutes_normal():
    e = make_etat(type_jour=TypeJour.POSTE)
    tranches = [Tranche(1, "S1", "06:00", "14:00"), Tranche(2, "S2", "15:00", "18:00")]
    wd = WorkDay(e.jour, e, tranches)
    assert wd.amplitude_minutes() == (18 - 6) * 60


def test_amplitude_with_midnight_passage():
    e = make_etat(type_jour=TypeJour.POSTE)
    tranches = [Tranche(1, "N1", "22:00", "06:00")]
    wd = WorkDay(e.jour, e, tranches)
    assert wd.amplitude_minutes() == 8 * 60  # 480 minutes


def test_start_and_end_time_helpers():
    tranches = [Tranche(1, "T1", "05:00", "11:00"), Tranche(2, "T2", "12:00", "15:00")]
    wd = WorkDay(date(2025, 1, 5), make_etat(), tranches)
    assert wd.start_time() == time(5, 0)
    assert wd.end_time() == time(15, 0)


# -------------------------------------------------------------------
# 3️⃣ Nocturnes
# -------------------------------------------------------------------

def test_is_nocturne_true_for_night_tranche():
    e = make_etat(type_jour=TypeJour.POSTE)
    tranches = [Tranche(1, "N1", "22:00", "06:00")]
    wd = WorkDay(e.jour, e, tranches)
    assert wd.is_nocturne()


def test_is_nocturne_false_for_day_tranche():
    e = make_etat(type_jour=TypeJour.POSTE)
    tranches = [Tranche(1, "D1", "08:00", "16:00")]
    wd = WorkDay(e.jour, e, tranches)
    assert not wd.is_nocturne()


# -------------------------------------------------------------------
# 4️⃣ Affichage & représentation
# -------------------------------------------------------------------

def test_str_representation_colored_and_complete():
    e = make_etat(type_jour=TypeJour.POSTE)
    wd = WorkDay(jour=date(2025, 3, 10), etat=e, tranches=make_tranches())

    s = strip_ansi(str(wd))
    assert "2025-03-10" in s
    assert "POSTE" in s
    assert "Tranches:" in s
    assert "MJ" in s


def test_str_representation_without_tranches():
    e = make_etat(type_jour=TypeJour.REPOS)
    wd = WorkDay(jour=date(2025, 3, 11), etat=e, tranches=[])
    s = strip_ansi(str(wd))
    assert "-" in s  # pas de tranches


# -------------------------------------------------------------------
# 5️⃣ Cas limites
# -------------------------------------------------------------------

def test_amplitude_zero_when_no_tranches():
    e = make_etat(type_jour=TypeJour.REPOS)
    wd = WorkDay(date(2025, 1, 1), e, [])
    assert wd.amplitude_minutes() == 0
    assert wd.amplitude_hours() == 0
    assert wd.start_time() is None
    assert wd.end_time() is None


def test_tranche_is_nocturne_edge_cases():
    e = make_etat(type_jour=TypeJour.POSTE)
    wd = WorkDay(e.jour, e, [])
    # tranche pile à 21:30 ou avant 6:30 = nocturne
    t1 = Tranche(1, "N", "21:30", "23:00")
    t2 = Tranche(2, "M", "05:00", "06:30")
    assert wd._tranche_is_nocturne(t1)
    assert wd._tranche_is_nocturne(t2)