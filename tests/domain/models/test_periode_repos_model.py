import pytest
from datetime import date, timedelta
from core.domain.models.periode_repos import PeriodeRepos


# -------------------------------------------------------
# from_days()
# -------------------------------------------------------

def test_from_days_single_day():
    d = date(2024, 1, 10)
    pr = PeriodeRepos.from_days([d])

    assert pr.start == d
    assert pr.end == d
    assert pr.nb_jours == 1
    assert pr.jours == [d]


def test_from_days_sorted_and_consecutive():
    d1 = date(2024, 1, 10)
    d2 = date(2024, 1, 11)

    pr = PeriodeRepos.from_days([d2, d1])  # test du tri
    assert pr.jours == [d1, d2]


def test_from_days_not_consecutive():
    d1 = date(2024, 1, 10)
    d2 = date(2024, 1, 12)

    with pytest.raises(ValueError):
        PeriodeRepos.from_days([d1, d2])


def test_from_days_empty():
    with pytest.raises(ValueError):
        PeriodeRepos.from_days([])


# -------------------------------------------------------
# Tests sur les propriétés
# -------------------------------------------------------

def test_duree_minutes_simple():
    base = date(2027, 1, 1)

    periode = PeriodeRepos.from_days([base])

    assert periode.duree_minutes == 2180

def test_duree_minutes_triple():
    base = [date(2027, 1, 1), date(2027, 1, 2), date(2027, 1, 3)]

    periode = PeriodeRepos.from_days(base)

    assert periode.duree_minutes == 5060

def test_is_simple_double_triple_4plus():
    base = date(2024, 1, 1)

    assert PeriodeRepos.from_days([base]).is_simple()
    assert PeriodeRepos.from_days(
        [base, base + timedelta(days=1)]
    ).is_double()
    assert PeriodeRepos.from_days(
        [base, base + timedelta(days=1), base + timedelta(days=2)]
    ).is_triple()
    assert PeriodeRepos.from_days(
        [base + timedelta(days=i) for i in range(4)]
    ).is_4plus()


def test_is_rpsd_1jours():
    # samedi = 6 janvier 2024
    sam = date(2024, 1, 6)

    pr = PeriodeRepos.from_days([sam])
    assert pr.is_rpsd() is False
    assert pr.is_werp() is False   # RPSD ⊂ WERP

def test_is_rpsd():
    # samedi = 6 janvier 2024
    sam = date(2024, 1, 6)
    dim = date(2024, 1, 7)

    pr = PeriodeRepos.from_days([sam, dim])
    assert pr.is_rpsd() is True
    assert pr.is_werp() is True   # RPSD ⊂ WERP


def test_is_werp_sam_dim():
    sam = date(2024, 1, 6)
    dim = date(2024, 1, 7)

    pr = PeriodeRepos.from_days([sam, dim])
    assert pr.is_werp() is True


def test_is_werp_dim_lun_mar():
    dim = date(2024, 1, 7)
    lun = date(2024, 1, 8)
    mar = date(2024, 1, 9)

    pr = PeriodeRepos.from_days([dim, lun, mar])
    assert pr.is_werp() is True
    assert pr.is_rpsd() is False

def test_is_werp_lun_mar_mer():
    lun = date(2024, 1, 8)
    mar = date(2024, 1, 9)
    mer = date(2024, 1, 10)

    pr = PeriodeRepos.from_days([lun, mar, mer])
    assert pr.is_werp() is False
    assert pr.is_rpsd() is False

def test_str_dim_lun_mar():
    dim = date(2024, 1, 7)
    lun = date(2024, 1, 8)
    mar = date(2024, 1, 9)

    pr = PeriodeRepos.from_days([dim, lun, mar])

    text = str(pr)

    assert "2024-01-07" in text
    assert "2024-01-09" in text
    assert "3j" in text