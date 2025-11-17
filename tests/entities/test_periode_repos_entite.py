from datetime import date, timedelta
from core.domain.models.periode_repos import PeriodeRepos


# -------------------------------------------------------------------
# 1️⃣ Création et propriétés de base
# -------------------------------------------------------------------

def test_periode_repos_creation_and_properties():
    jours = [date(2025, 1, 10), date(2025, 1, 11)]
    pr = PeriodeRepos(start=jours[0], end=jours[-1], jours=jours)

    assert pr.start == date(2025, 1, 10)
    assert pr.end == date(2025, 1, 11)
    assert pr.nb_jours == 2
    assert isinstance(pr.duree_minutes, int)
    assert pr.duree_minutes > 0


# -------------------------------------------------------------------
# 2️⃣ Calcul de la durée totale
# -------------------------------------------------------------------

def test_duree_minutes_calculations():
    # 1 jour → 24h + 12h20 = 36h20 = 2180 minutes
    pr1 = PeriodeRepos(date(2025, 1, 1), date(2025, 1, 1), [date(2025, 1, 1)])
    assert pr1.duree_minutes == (24 * 60) + (12 * 60 + 20)

    # 2 jours → 48h + 12h20 = 60h20 = 3620 minutes
    jours = [date(2025, 1, 1) + timedelta(days=i) for i in range(2)]
    pr2 = PeriodeRepos(jours[0], jours[-1], jours)
    assert pr2.duree_minutes == (2 * 24 * 60) + (12 * 60 + 20)

    # 3 jours → 72h + 12h20 = 84h20 = 5060 minutes
    jours = [date(2025, 1, 1) + timedelta(days=i) for i in range(3)]
    pr3 = PeriodeRepos(jours[0], jours[-1], jours)
    assert pr3.duree_minutes == (3 * 24 * 60) + (12 * 60 + 20)


# -------------------------------------------------------------------
# 3️⃣ Labelisation (RP simple/double/triple/...)
# -------------------------------------------------------------------

def test_label_variants():
    pr1 = PeriodeRepos(date(2025, 1, 1), date(2025, 1, 1), [date(2025, 1, 1)])
    assert pr1.label() == "RP simple"

    jours2 = [date(2025, 1, 1), date(2025, 1, 2)]
    pr2 = PeriodeRepos(jours2[0], jours2[-1], jours2)
    assert pr2.label() == "RP double"

    jours3 = [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)]
    pr3 = PeriodeRepos(jours3[0], jours3[-1], jours3)
    assert pr3.label() == "RP triple"

    jours5 = [date(2025, 1, 1) + timedelta(days=i) for i in range(5)]
    pr5 = PeriodeRepos(jours5[0], jours5[-1], jours5)
    assert pr5.label() == "RP 5 jours"


# -------------------------------------------------------------------
# 4️⃣ Représentation textuelle
# -------------------------------------------------------------------

def test_str_representation():
    jours = [date(2025, 2, 1), date(2025, 2, 2)]
    pr = PeriodeRepos(jours[0], jours[-1], jours)
    s = str(pr)

    assert "RP double" in s
    assert "2025-02-01" in s
    assert "2025-02-02" in s
    assert "2j" in s
