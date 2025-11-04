import pytest
from datetime import date, time, timedelta, datetime
from core.utils import time_helpers as th


def test_combine_datetime():
    jour = date(2025, 1, 1)
    heure = time(10, 30)
    dt = th.combine_datetime(jour, heure)
    assert isinstance(dt, datetime)
    assert dt.date() == jour
    assert dt.time() == heure


def test_end_datetime_with_rollover_same_day():
    jour = date(2025, 1, 1)
    debut = time(8, 0)
    fin = time(16, 0)
    dt_fin = th.end_datetime_with_rollover(jour, debut, fin)
    assert dt_fin == datetime(2025, 1, 1, 16, 0)


def test_end_datetime_with_rollover_next_day():
    jour = date(2025, 1, 1)
    debut = time(22, 0)
    fin = time(6, 0)
    dt_fin = th.end_datetime_with_rollover(jour, debut, fin)
    assert dt_fin == datetime(2025, 1, 2, 6, 0)


def test_duration_hours_between_normal_and_rollover():
    h1 = time(8, 0)
    h2 = time(10, 30)
    assert th.duration_hours_between(h1, h2) == pytest.approx(2.5)

    # Passage minuit
    h1 = time(22, 0)
    h2 = time(6, 0)
    assert th.duration_hours_between(h1, h2) == pytest.approx(8.0)


def test_overlap_hours_partial_and_full_overlap():
    # Période partiellement chevauchée
    p1 = (time(8, 0), time(12, 0))
    p2 = (time(10, 0), time(14, 0))
    assert th.overlap_hours(p1, p2) == pytest.approx(2.0)

    # Période entièrement incluse
    p1 = (time(8, 0), time(16, 0))
    p2 = (time(9, 0), time(15, 0))
    assert th.overlap_hours(p1, p2) == pytest.approx(6.0)

    # Sans chevauchement
    p1 = (time(8, 0), time(10, 0))
    p2 = (time(11, 0), time(12, 0))
    assert th.overlap_hours(p1, p2) == 0.0

    # Passage minuit : ici, selon ta logique, pas de chevauchement réel
    p1 = (time(22, 0), time(2, 0))
    p2 = (time(1, 0), time(3, 0))
    assert th.overlap_hours(p1, p2) == 0.0


def test_is_tranche_nocturne():
    assert th.is_tranche_nocturne(time(22, 0), time(6, 0))
    assert th.is_tranche_nocturne(time(23, 0), time(7, 0))
    assert th.is_tranche_nocturne(time(21, 30), time(22, 0))
    assert th.is_tranche_nocturne(time(5, 30), time(6, 30))
    assert not th.is_tranche_nocturne(time(7, 0), time(14, 0))


@pytest.mark.parametrize(
    "minutes,expected",
    [
        (90, "1h30"),
        (480, "8h"),
        (15, "15min"),
        (0, "0min"),
        (None, "—"),
        (125, "2h05"),
    ],
)
def test_minutes_to_duree_str(minutes, expected):
    assert th.minutes_to_duree_str(minutes) == expected
