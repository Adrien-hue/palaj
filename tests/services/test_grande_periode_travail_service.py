import pytest
from datetime import date, timedelta

from core.domain.entities import EtatJourAgent, TypeJour
from core.domain.models.work_day import WorkDay
from core.domain.services.grande_periode_travail_service import GrandePeriodeTravailService
from core.domain.contexts.planning_context import PlanningContext


@pytest.fixture
def service():
    return GrandePeriodeTravailService()


def make_wd(jour, type_jour):
    """Crée un WorkDay simplifié avec un EtatJourAgent factice."""
    etat = EtatJourAgent(agent_id=1, jour=jour, type_jour=type_jour)
    return WorkDay(jour=jour, etat=etat, tranches=[])


@pytest.fixture
def base_dates():
    """Retourne une séquence de dates continues pour faciliter les tests."""
    start = date(2025, 1, 1)
    return [start + timedelta(days=i) for i in range(10)]


# ------------------------------------------------------------------
# 1️⃣ Cas de base — aucune journée
# ------------------------------------------------------------------

def test_detect_gpts_empty_context(service):
    context = PlanningContext(agent=None, work_days=[], date_reference=date(2025, 1, 1))
    gpts = service.detect_gpts(context)
    assert gpts == []


# ------------------------------------------------------------------
# 2️⃣ GPT normale (suite de jours travaillés encadrée par repos)
# ------------------------------------------------------------------

def test_detect_gpt_normale(service, base_dates):
    wd = [
        make_wd(base_dates[0], TypeJour.REPOS),
        make_wd(base_dates[1], TypeJour.POSTE),
        make_wd(base_dates[2], TypeJour.POSTE),
        make_wd(base_dates[3], TypeJour.REPOS),
    ]
    context = PlanningContext(agent=None, work_days=wd, date_reference=base_dates[0])

    gpts = service.detect_gpts(context)

    assert len(gpts) == 1
    gpt = gpts[0]
    assert gpt.start == base_dates[1]
    assert gpt.end == base_dates[2]
    assert gpt.nb_jours == 2
    assert gpt.is_complete


# ------------------------------------------------------------------
# 3️⃣ GPT avec ZCOT (devrait être reconnue comme travail)
# ------------------------------------------------------------------

def test_detect_gpt_avec_zcot(service, base_dates):
    wd = [
        make_wd(base_dates[0], TypeJour.REPOS),
        make_wd(base_dates[1], TypeJour.ZCOT),
        make_wd(base_dates[2], TypeJour.REPOS),
    ]
    context = PlanningContext(agent=None, work_days=wd, date_reference=base_dates[0])

    gpts = service.detect_gpts(context)
    assert len(gpts) == 1
    gpt = gpts[0]
    assert gpt.has_zcot
    assert not gpt.has_poste
    assert gpt.is_complete


# ------------------------------------------------------------------
# 4️⃣ GPT avec absence et congé entre jours travaillés
# ------------------------------------------------------------------

def test_detect_gpt_melange_absence_conge(service, base_dates):
    wd = [
        make_wd(base_dates[0], TypeJour.REPOS),
        make_wd(base_dates[1], TypeJour.POSTE),
        make_wd(base_dates[2], TypeJour.ABSENCE),
        make_wd(base_dates[3], TypeJour.CONGE),
        make_wd(base_dates[4], TypeJour.ZCOT),
        make_wd(base_dates[5], TypeJour.REPOS),
    ]
    context = PlanningContext(agent=None, work_days=wd, date_reference=base_dates[0])

    gpts = service.detect_gpts(context)
    assert len(gpts) == 1
    gpt = gpts[0]
    assert gpt.nb_jours == 4
    assert gpt.is_mixed()
    assert gpt.category() == "Mixte"


# ------------------------------------------------------------------
# 5️⃣ GPT tronquée à gauche (commence dès le début du contexte)
# ------------------------------------------------------------------

def test_detect_gpt_tronquee_gauche(service, base_dates):
    wd = [
        make_wd(base_dates[0], TypeJour.POSTE),
        make_wd(base_dates[1], TypeJour.POSTE),
        make_wd(base_dates[2], TypeJour.REPOS),
    ]
    context = PlanningContext(agent=None, work_days=wd, date_reference=base_dates[0])

    gpts = service.detect_gpts(context)

    assert len(gpts) == 1
    gpt = gpts[0]
    assert gpt.is_left_truncated
    assert not gpt.is_right_truncated
    assert gpt.start == base_dates[0]


# ------------------------------------------------------------------
# 6️⃣ GPT tronquée à droite (finit à la fin du contexte)
# ------------------------------------------------------------------

def test_detect_gpt_tronquee_droite(service, base_dates):
    wd = [
        make_wd(base_dates[0], TypeJour.REPOS),
        make_wd(base_dates[1], TypeJour.POSTE),
        make_wd(base_dates[2], TypeJour.ZCOT),
    ]
    context = PlanningContext(agent=None, work_days=wd, date_reference=base_dates[0])

    gpts = service.detect_gpts(context)

    assert len(gpts) == 1
    gpt = gpts[0]
    assert not gpt.is_left_truncated
    assert gpt.is_right_truncated
    assert gpt.end == base_dates[2]


# ------------------------------------------------------------------
# 7️⃣ GPT avec deux blocs distincts (deux GPT détectées)
# ------------------------------------------------------------------

def test_detect_deux_gpts(service, base_dates):
    wd = [
        make_wd(base_dates[0], TypeJour.REPOS),
        make_wd(base_dates[1], TypeJour.POSTE),
        make_wd(base_dates[2], TypeJour.REPOS),
        make_wd(base_dates[3], TypeJour.ZCOT),
        make_wd(base_dates[4], TypeJour.REPOS),
    ]
    context = PlanningContext(agent=None, work_days=wd, date_reference=base_dates[0])

    gpts = service.detect_gpts(context)

    assert len(gpts) == 2
    assert gpts[0].start == base_dates[1]
    assert gpts[1].start == base_dates[3]


# ------------------------------------------------------------------
# 8️⃣ GPT vide ou incohérente (aucun jour non-repos)
# ------------------------------------------------------------------

def test_detect_aucune_gpt(service, base_dates):
    wd = [make_wd(d, TypeJour.REPOS) for d in base_dates[:5]]
    context = PlanningContext(agent=None, work_days=wd, date_reference=base_dates[0])
    gpts = service.detect_gpts(context)
    assert gpts == []
