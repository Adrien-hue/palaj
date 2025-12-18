# tests/domain/models/test_work_day.py
from datetime import date, time

from core.domain.entities import TypeJour
from core.domain.models.work_day import WorkDay


def test_work_day_type_detection_and_duration_for_poste(make_tranche):
    tranche = make_tranche(heure_debut="08:00", heure_fin="12:00")
    wd = WorkDay(jour=date(2025, 1, 1), tranches=[tranche])

    assert wd.type() is TypeJour.POSTE
    assert wd.is_working()
    assert wd.duree_minutes() == tranche.duree_minutes()
    assert wd.amplitude_minutes() == 240
    assert wd.start_time() == time(8, 0)
    assert wd.end_time() == time(12, 0)


def test_work_day_detects_nocturne_and_cross_midnight_amplitude(make_tranche):
    tranche = make_tranche(heure_debut="22:00", heure_fin="06:00", nom="N")
    wd = WorkDay(jour=date(2025, 1, 1), tranches=[tranche])

    assert wd.is_nocturne()
    # 22:00 → 06:00 = 8h
    assert wd.amplitude_minutes() == 8 * 60


def test_work_day_with_etat_overrides_type_and_duration(make_etat_jour_agent):
    etat = make_etat_jour_agent(jour=date(2025, 1, 1), type_jour=TypeJour.ZCOT)
    wd = WorkDay(jour=date(2025, 1, 1), etat=etat)

    assert wd.type() is TypeJour.ZCOT
    assert wd.duree_minutes() == 7 * 60  # 7h fixées
    assert wd.duree_hours() == 12.0      # comportement actuel de duree_hours()


def test_work_day_rest_and_absence_flags(make_etat_jour_agent):
    rest = WorkDay(
        jour=date(2024, 1, 4),
        etat=make_etat_jour_agent(jour=date(2024, 1, 4), type_jour=TypeJour.REPOS),
    )
    absence = WorkDay(
        jour=date(2024, 1, 5),
        etat=make_etat_jour_agent(jour=date(2024, 1, 5), type_jour=TypeJour.ABSENCE),
    )

    assert rest.is_rest() is True
    assert rest.duree_minutes() == 0
    assert absence.is_absence() is True


def test_work_day_string_and_repr(make_tranche):
    tranche = make_tranche(heure_debut="07:00", heure_fin="09:00", nom="M")
    wd = WorkDay(jour=date(2024, 1, 6), tranches=[tranche])

    text = str(wd)
    assert "2024-01-06" in text
    assert "POSTE" in text
    assert "2h" in text
    assert "WorkDay(2024-01-06" in repr(wd)


def test_nocturne_false_no_tranche():
    wd = WorkDay(date(2025, 1, 1), tranches=[])
    assert wd.is_nocturne() is False


def test_nocturne_true(make_tranche):
    t = make_tranche(heure_debut="22:00", heure_fin="06:00", nom="N")
    wd = WorkDay(date(2025, 1, 1), tranches=[t])
    assert wd.is_nocturne() is True


def test_nocturne_false_daytime(make_tranche):
    t = make_tranche(heure_debut="10:00", heure_fin="12:00", nom="N")
    wd = WorkDay(date(2025, 1, 1), tranches=[t])
    assert wd.is_nocturne() is False


def test_amplitude_zero_if_no_tranche():
    wd = WorkDay(date(2025, 1, 1), tranches=[])
    assert wd.amplitude_minutes() == 0


def test_amplitude_simple(make_tranche):
    t = make_tranche(heure_debut="08:00", heure_fin="12:00", nom="N")
    wd = WorkDay(date(2025, 1, 1), tranches=[t])
    assert wd.amplitude_minutes() == 240


def test_amplitude_midnight_wrap(make_tranche):
    # ex : 22:00 → 05:00 => 7h => 420 min
    t = make_tranche(heure_debut="22:00", heure_fin="05:00", nom="N")
    wd = WorkDay(date(2025, 1, 1), tranches=[t])
    assert wd.amplitude_minutes() == 7 * 60


def test_amplitude_hours(make_tranche):
    t = make_tranche(heure_debut="10:00", heure_fin="13:00", nom="N")
    wd = WorkDay(date(2025, 1, 1), tranches=[t])
    assert wd.amplitude_hours() == 3


def test_duree_minutes_zcot(make_etat_jour_agent):
    wd = WorkDay(
        date(2025, 1, 1),
        etat=make_etat_jour_agent(jour=date(2025, 1, 1), type_jour=TypeJour.ZCOT),
    )
    assert wd.duree_minutes() == 7 * 60


def test_duree_minutes_poste(make_tranche):
    t1 = make_tranche(heure_debut="08:00", heure_fin="12:00", nom="N")
    t2 = make_tranche(heure_debut="13:00", heure_fin="16:00", nom="N")
    wd = WorkDay(date(2025, 1, 1), tranches=[t1, t2])
    assert wd.duree_minutes() == (4 + 3) * 60  # 7h = 420min


def test_duree_minutes_rest(make_etat_jour_agent):
    wd = WorkDay(
        date(2025, 1, 1),
        etat=make_etat_jour_agent(jour=date(2025, 1, 1), type_jour=TypeJour.REPOS),
    )
    assert wd.duree_minutes() == 0


def test_duree_hours_zcot(make_etat_jour_agent):
    wd = WorkDay(
        date(2025, 1, 1),
        etat=make_etat_jour_agent(jour=date(2025, 1, 1), type_jour=TypeJour.ZCOT),
    )
    assert wd.duree_hours() == 12.0


def test_duree_hours_poste(make_tranche):
    t = make_tranche(heure_debut="08:00", heure_fin="11:00", nom="N")
    wd = WorkDay(date(2025, 1, 1), tranches=[t])
    assert wd.duree_hours() == 3.0


def test_duree_hours_other(make_etat_jour_agent):
    wd = WorkDay(
        date(2025, 1, 1),
        etat=make_etat_jour_agent(jour=date(2025, 1, 1), type_jour=TypeJour.ABSENCE),
    )
    assert wd.duree_hours() == 0.0


def test_start_time_end_time(make_tranche):
    t1 = make_tranche(heure_debut="09:00", heure_fin="12:00", nom="N")
    t2 = make_tranche(heure_debut="07:00", heure_fin="10:00", nom="N")
    wd = WorkDay(date(2025, 1, 1), tranches=[t1, t2])

    assert wd.start_time() == time(7, 0)
    assert wd.end_time() == time(12, 0)


def test_start_time_none():
    wd = WorkDay(date(2025, 1, 1), tranches=[])
    assert wd.start_time() is None
    assert wd.end_time() is None


def test_str_contains_color_and_data(make_tranche):
    t = make_tranche(heure_debut="08:00", heure_fin="09:00", nom="T1")
    d = date(2025, 1, 1)
    wd = WorkDay(d, tranches=[t])

    s = str(wd)

    assert "2025-01-01" in s
    assert "POSTE" in s
    assert "T1" in s
    assert "\033[" in s  # présence d’ANSI color
