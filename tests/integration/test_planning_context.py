import pytest
from datetime import date, time, timedelta
from core.domain.contexts.planning_context import PlanningContext
from core.domain.entities.work_day import WorkDay
from core.domain.entities import TypeJour
from core.domain.entities.agent import Agent

# ---------------------------------------------------------------------------
# Fixtures utilitaires
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_agent():
    return Agent(id=1, nom="Durand", prenom="Alice")


@pytest.fixture
def sample_work_days():
    """
    Construit un ensemble de WorkDays représentatifs :
    - 1er janv : poste (jour travaillé)
    - 2 janv   : repos
    - 3 janv   : zcot (jour travaillé)
    - 4 janv   : poste (jour travaillé, traverse minuit)
    """
    wd1 = WorkDay(date(2025, 1, 1))
    wd1.type = lambda: TypeJour.POSTE
    wd1.is_working = lambda: True
    wd1.start_time = lambda: time(8, 0)
    wd1.end_time = lambda: time(16, 0)
    wd1.duree_minutes = lambda: 480  # 8h
    wd1.amplitude_minutes = lambda: 480

    wd2 = WorkDay(date(2025, 1, 2))
    wd2.type = lambda: TypeJour.REPOS
    wd2.is_working = lambda: False
    wd2.start_time = lambda: None
    wd2.end_time = lambda: None
    wd2.duree_minutes = lambda: 0
    wd2.amplitude_minutes = lambda: 0

    wd3 = WorkDay(date(2025, 1, 3))
    wd3.type = lambda: TypeJour.ZCOT
    wd3.is_working = lambda: True
    wd3.start_time = lambda: time(9, 0)
    wd3.end_time = lambda: time(17, 0)
    wd3.duree_minutes = lambda: 420
    wd3.amplitude_minutes = lambda: 480

    wd4 = WorkDay(date(2025, 1, 4))
    wd4.type = lambda: TypeJour.POSTE
    wd4.is_working = lambda: True
    wd4.start_time = lambda: time(22, 0)
    wd4.end_time = lambda: time(6, 20)
    wd4.duree_minutes = lambda: 500
    wd4.amplitude_minutes = lambda: 500

    return [wd1, wd2, wd3, wd4]


@pytest.fixture
def context(fake_agent, sample_work_days):
    return PlanningContext(agent=fake_agent, work_days=sample_work_days)


# ---------------------------------------------------------------------------
# Tests unitaires
# ---------------------------------------------------------------------------

def test_start_end_dates(context):
    """Vérifie que le contexte détermine correctement ses bornes."""
    assert context.start_date == date(2025, 1, 1)
    assert context.end_date == date(2025, 1, 4)


def test_get_work_day(context):
    """Vérifie la récupération d'un WorkDay spécifique."""
    wd = context.get_work_day(date(2025, 1, 3))
    assert wd is not None
    assert wd.jour == date(2025, 1, 3)

    assert context.get_work_day(date(2025, 2, 1)) is None


def test_previous_next_working_day(context):
    """Vérifie la navigation avant/après pour jours travaillés."""
    wd = context.get_work_day(date(2025, 1, 3))

    prev = context.get_previous_working_day(wd.jour)
    assert prev.jour == date(2025, 1, 1)

    nxt = context.get_next_working_day(wd.jour)
    assert nxt.jour == date(2025, 1, 4)


def test_gap_calculations(context):
    """Teste les calculs d'écart entre jours travaillés."""
    gap_prev = context.get_last_working_day_gap(date(2025, 1, 3))
    assert gap_prev == 2  # entre 1er et 3 janv

    gap_next = context.get_next_working_day_gap(date(2025, 1, 1))
    assert gap_next == 2


def test_repos_minutes_since_last_work_day(context):
    """Teste le calcul des minutes de repos entre deux jours travaillés."""
    minutes = context.get_repos_minutes_since_last_work_day(date(2025, 1, 3))
    assert minutes == (24 * 60) + (17 * 60)  # 41h → 2460 min

    # Test de passage minuit (22h → 6h20)
    minutes2 = context.get_repos_minutes_since_last_work_day(date(2025, 1, 4))
    # Fin du 3 janv = 17h, début du 4 = 22h → 29h = 1740 min
    assert 1700 < minutes2 < 1780


def test_total_hours_and_amplitude(context):
    """Vérifie le total d'heures et l'amplitude journalière."""
    total_h = context.get_total_hours_for_period()
    assert round(total_h, 2) == pytest.approx((480 + 420 + 500) / 60, rel=0.01)

    amplitude = context.get_amplitude_for_day(date(2025, 1, 1))
    assert amplitude == 480


def test_get_gpt_segments(context):
    """Teste la détection des GPT (séquences de jours travaillés)."""
    gpts = context.get_gpt_segments()
    assert len(gpts) == 2  # [1er janv], [3-4 janv]
    assert [wd.jour for wd in gpts[0]] == [date(2025, 1, 1)]
    assert [wd.jour for wd in gpts[1]] == [date(2025, 1, 3), date(2025, 1, 4)]


def test_set_date_reference(context):
    """Vérifie la mise à jour de la date de référence."""
    new_date = date(2025, 2, 1)
    context.set_date_reference(new_date)
    assert context.date_reference == new_date


def test_from_planning(mocker, fake_agent, sample_work_days):
    """Vérifie la construction d'un PlanningContext depuis un AgentPlanning."""
    fake_planning = mocker.Mock()
    fake_planning.get_agent.return_value = fake_agent
    fake_planning.get_work_days.return_value = sample_work_days
    fake_planning.get_start_date.return_value = date(2025, 1, 1)

    ctx = PlanningContext.from_planning(fake_planning)

    assert isinstance(ctx, PlanningContext)
    assert ctx.agent == fake_agent
    assert len(ctx.work_days) == len(sample_work_days)
    assert ctx.date_reference == date(2025, 1, 1)
