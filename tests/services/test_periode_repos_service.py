import pytest
from datetime import date, timedelta

from core.domain.services.periode_repos_service import PeriodeReposService
from core.domain.entities import EtatJourAgent, TypeJour
from core.domain.entities.work_day import WorkDay
from core.domain.entities.periode_repos import PeriodeRepos
from core.domain.contexts.planning_context import PlanningContext


@pytest.fixture
def service():
    return PeriodeReposService()


def make_wd(jour, type_jour):
    """Crée un WorkDay factice avec l’état approprié."""
    etat = EtatJourAgent(agent_id=1, jour=jour, type_jour=type_jour)
    return WorkDay(jour=jour, etat=etat, tranches=[])


@pytest.fixture
def base_dates():
    start = date(2025, 1, 1)
    return [start + timedelta(days=i) for i in range(10)]


# ------------------------------------------------------------------
# 1️⃣ Aucun repos
# ------------------------------------------------------------------
def test_aucun_repos(service, base_dates):
    wds = [make_wd(d, TypeJour.POSTE) for d in base_dates]
    context = PlanningContext(agent=None, work_days=wds, date_reference=base_dates[0])
    periodes = service.detect_periodes_repos(context)
    assert periodes == []


# ------------------------------------------------------------------
# 2️⃣ Un seul jour de repos → RP simple
# ------------------------------------------------------------------
def test_un_repos_simple(service, base_dates):
    wds = [
        make_wd(base_dates[0], TypeJour.POSTE),
        make_wd(base_dates[1], TypeJour.REPOS),
        make_wd(base_dates[2], TypeJour.POSTE),
    ]
    context = PlanningContext(agent=None, work_days=wds, date_reference=base_dates[0])
    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 1
    rp = periodes[0]
    assert rp.start == base_dates[1]
    assert rp.end == base_dates[1]
    assert rp.nb_jours == 1
    assert rp.label() == "RP simple"


# ------------------------------------------------------------------
# 3️⃣ Deux jours consécutifs → RP double
# ------------------------------------------------------------------
def test_repos_double(service, base_dates):
    wds = [
        make_wd(base_dates[0], TypeJour.POSTE),
        make_wd(base_dates[1], TypeJour.REPOS),
        make_wd(base_dates[2], TypeJour.REPOS),
        make_wd(base_dates[3], TypeJour.POSTE),
    ]
    context = PlanningContext(agent=None, work_days=wds, date_reference=base_dates[0])
    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 1
    rp = periodes[0]
    assert rp.nb_jours == 2
    assert rp.label() == "RP double"
    assert rp.start == base_dates[1]
    assert rp.end == base_dates[2]


# ------------------------------------------------------------------
# 4️⃣ Trois jours consécutifs → RP triple
# ------------------------------------------------------------------
def test_repos_triple(service, base_dates):
    wds = [
        make_wd(base_dates[0], TypeJour.REPOS),
        make_wd(base_dates[1], TypeJour.REPOS),
        make_wd(base_dates[2], TypeJour.REPOS),
        make_wd(base_dates[3], TypeJour.POSTE),
    ]
    context = PlanningContext(agent=None, work_days=wds, date_reference=base_dates[0])
    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 1
    rp = periodes[0]
    assert rp.nb_jours == 3
    assert rp.label() == "RP triple"
    assert rp.duree_minutes > 0  # test la méthode


# ------------------------------------------------------------------
# 5️⃣ Deux blocs séparés → deux périodes distinctes
# ------------------------------------------------------------------
def test_deux_blocs_repos(service, base_dates):
    wds = [
        make_wd(base_dates[0], TypeJour.REPOS),
        make_wd(base_dates[1], TypeJour.REPOS),
        make_wd(base_dates[2], TypeJour.POSTE),
        make_wd(base_dates[3], TypeJour.REPOS),
        make_wd(base_dates[4], TypeJour.POSTE),
    ]
    context = PlanningContext(agent=None, work_days=wds, date_reference=base_dates[0])
    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 2
    assert periodes[0].start == base_dates[0]
    assert periodes[0].end == base_dates[1]
    assert periodes[1].start == base_dates[3]


# ------------------------------------------------------------------
# 6️⃣ Période de repos de plus de 3 jours → RP X jours
# ------------------------------------------------------------------
def test_repos_long(service, base_dates):
    wds = [make_wd(d, TypeJour.REPOS) for d in base_dates[:5]]
    context = PlanningContext(agent=None, work_days=wds, date_reference=base_dates[0])
    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 1
    rp = periodes[0]
    assert rp.nb_jours == 5
    assert rp.label() == "RP 5 jours"
    assert "RP 5 jours" in str(rp)
    assert rp.start == base_dates[0]
    assert rp.end == base_dates[4]


# ------------------------------------------------------------------
# 7️⃣ Repos non consécutifs → plusieurs RP simples
# ------------------------------------------------------------------
def test_repos_non_consecutifs(service, base_dates):
    wds = [
        make_wd(base_dates[0], TypeJour.REPOS),
        make_wd(base_dates[1], TypeJour.POSTE),
        make_wd(base_dates[2], TypeJour.REPOS),
        make_wd(base_dates[3], TypeJour.POSTE),
    ]
    context = PlanningContext(agent=None, work_days=wds, date_reference=base_dates[0])
    periodes = service.detect_periodes_repos(context)

    assert len(periodes) == 2
    assert all(rp.nb_jours == 1 for rp in periodes)
    assert all(rp.label() == "RP simple" for rp in periodes)
