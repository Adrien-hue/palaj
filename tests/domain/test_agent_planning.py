import pytest
from datetime import date, time, timedelta
from types import SimpleNamespace

from core.domain.entities import Agent, EtatJourAgent, Affectation, Tranche, TypeJour
from core.agent_planning import AgentPlanning


# --------------------------------------------------------
# 🔧 FIXTURES
# --------------------------------------------------------
@pytest.fixture
def fake_agent():
    return Agent(id=1, prenom="Alice", nom="Durand")


@pytest.fixture
def fake_tranche():
    return Tranche(id=1, nom="J1", heure_debut=time(8, 0), heure_fin=time(16, 0), poste_id=1)


@pytest.fixture
def fake_etats():
    """3 jours : travail, repos, zcot"""
    return [
        EtatJourAgent(agent_id=1, jour=date(2025, 1, 1), type_jour=TypeJour.POSTE),
        EtatJourAgent(agent_id=1, jour=date(2025, 1, 2), type_jour=TypeJour.REPOS),
        EtatJourAgent(agent_id=1, jour=date(2025, 1, 3), type_jour=TypeJour.ZCOT),
    ]


@pytest.fixture
def fake_affectations():
    """2 affectations correspondant au 1er et 3e jour."""
    return [
        Affectation(agent_id=1, tranche_id=1, jour=date(2025, 1, 1)),
        Affectation(agent_id=1, tranche_id=1, jour=date(2025, 1, 3)),
    ]


# --------------------------------------------------------
# 🔧 REPOSITORIES MOCKÉS
# --------------------------------------------------------
@pytest.fixture
def mock_repos(mocker, fake_etats, fake_affectations, fake_tranche):
    """Mock complet des repositories utilisés par AgentPlanning."""
    affect_repo = mocker.Mock()
    affect_repo.list_for_agent.return_value = fake_affectations

    etat_repo = mocker.Mock()
    etat_repo.list_for_agent.return_value = fake_etats
    etat_repo.list_travail_for_agent.return_value = [fake_etats[0]]
    etat_repo.list_repos_for_agent.return_value = [fake_etats[1]]
    etat_repo.list_zcot_for_agent.return_value = [fake_etats[2]]
    etat_repo.list_absences_for_agent.return_value = []
    etat_repo.list_conges_for_agent.return_value = []

    poste_repo = mocker.Mock()
    qualif_repo = mocker.Mock()
    tranche_repo = mocker.Mock()
    tranche_repo.get.return_value = fake_tranche

    return SimpleNamespace(
        affect=affect_repo,
        etat=etat_repo,
        poste=poste_repo,
        qualif=qualif_repo,
        tranche=tranche_repo,
    )


# --------------------------------------------------------
# 🧩 TESTS UNITAIRES DE BASE
# --------------------------------------------------------

def test_init_and_build_workdays(fake_agent, mock_repos):
    """Vérifie que l'initialisation charge correctement les WorkDays."""
    planning = AgentPlanning(
        agent=fake_agent,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 3),
        affectation_repo=mock_repos.affect,
        etat_jour_agent_repo=mock_repos.etat,
        poste_repo=mock_repos.poste,
        qualification_repo=mock_repos.qualif,
        tranche_repo=mock_repos.tranche,
    )

    work_days = planning.get_work_days()
    assert len(work_days) == 3
    assert any(wd.etat is not None and wd.etat.type_jour == TypeJour.REPOS for wd in work_days)
    assert any(len(wd.tranches) > 0 for wd in work_days)


def test_getters(fake_agent, mock_repos):
    """Teste les méthodes getter de base."""
    planning = AgentPlanning(
        agent=fake_agent,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 3),
        affectation_repo=mock_repos.affect,
        etat_jour_agent_repo=mock_repos.etat,
        poste_repo=mock_repos.poste,
        qualification_repo=mock_repos.qualif,
        tranche_repo=mock_repos.tranche,
    )

    assert planning.get_agent().nom == "Durand"
    assert planning.get_start_date() == date(2025, 1, 1)
    assert planning.get_end_date() == date(2025, 1, 3)
    assert len(planning.get_affectations()) == 2
    assert len(planning.get_etats()) == 3
    assert len(planning.get_travail_jours()) == 1
    assert len(planning.get_repos_jours()) == 1
    assert len(planning.get_zcot_jours()) == 1


def test_total_heures_travaillees(fake_agent, mock_repos, fake_tranche):
    """Vérifie le calcul des heures travaillées."""
    mock_repos.tranche.get.return_value = fake_tranche
    planning = AgentPlanning(
        fake_agent, date(2025, 1, 1), date(2025, 1, 3),
        mock_repos.affect, mock_repos.etat, mock_repos.poste,
        mock_repos.qualif, mock_repos.tranche
    )

    total = planning.get_total_heures_travaillees()
    # 2 jours * 8h tranche + 1 jour ZCOT * 8h = 24h
    assert total == 24.0


def test_dimanches_stats(fake_agent, mock_repos, fake_etats):
    """Vérifie le comptage des dimanches travaillés."""
    # Positionne un dimanche dans la période
    start = date(2025, 1, 5)  # dimanche
    end = date(2025, 1, 5)

    mock_repos.etat.list_travail_for_agent.return_value = [
        EtatJourAgent(agent_id=1, jour=start, type_jour=TypeJour.POSTE)
    ]
    mock_repos.etat.list_zcot_for_agent.return_value = []

    planning = AgentPlanning(
        fake_agent, start, end,
        mock_repos.affect, mock_repos.etat, mock_repos.poste,
        mock_repos.qualif, mock_repos.tranche
    )

    worked, total = planning.get_dimanches_stats()
    assert total == 1
    assert worked == 1


def test_iter_jours(fake_agent, mock_repos):
    """Vérifie que l'itération sur les jours retourne les bonnes données."""
    planning = AgentPlanning(
        fake_agent, date(2025, 1, 1), date(2025, 1, 3),
        mock_repos.affect, mock_repos.etat, mock_repos.poste,
        mock_repos.qualif, mock_repos.tranche
    )

    days = list(planning.iter_jours())
    assert len(days) == 3
    assert isinstance(days[0][0], date)
    assert isinstance(days[0][1], list)
    assert isinstance(days[0][2], list)


def test_print_detailed_planning_output(fake_agent, mock_repos, capsys):
    """Vérifie que l'affichage détaillé ne crash pas et contient les bons jours."""
    planning = AgentPlanning(
        fake_agent, date(2025, 1, 1), date(2025, 1, 3),
        mock_repos.affect, mock_repos.etat, mock_repos.poste,
        mock_repos.qualif, mock_repos.tranche
    )

    planning.print_detailed_planning()
    output = capsys.readouterr().out
    assert "Planning détaillé" in output
    assert "Repos" in output or "J1" in output


def test_summary_output(fake_agent, mock_repos, capsys):
    """Vérifie que le résumé du planning contient les infos attendues."""
    fake_agent.get_qualifications = lambda repo: []

    planning = AgentPlanning(
        fake_agent, date(2025, 1, 1), date(2025, 1, 3),
        mock_repos.affect, mock_repos.etat, mock_repos.poste,
        mock_repos.qualif, mock_repos.tranche
    )

    planning.summary()
    output = capsys.readouterr().out
    assert "Planning de Alice Durand" in output
    assert "Heures travaillées" in output

def test_get_all_coverage_rates(fake_agent, mock_repos, mocker):
    """Teste le calcul du taux de couverture par poste."""
    fake_poste = mocker.Mock()
    fake_poste.nom = "Accueil"
    fake_poste.get_tranches.return_value = [mock_repos.tranche.get.return_value]

    fake_qualification = mocker.Mock()
    fake_qualification.get_poste.return_value = fake_poste

    # Mock la méthode de l'agent
    fake_agent.get_qualifications = lambda repo: [fake_qualification]

    planning = AgentPlanning(
        fake_agent, date(2025, 1, 1), date(2025, 1, 3),
        mock_repos.affect, mock_repos.etat, mock_repos.poste,
        mock_repos.qualif, mock_repos.tranche
    )

    rates = planning.get_all_coverage_rates()

    assert "Accueil" in rates
    # 2 affectations sur 3 jours * 1 tranche = 2/3 → 66.7 %
    assert rates["Accueil"] == pytest.approx(66.7, rel=0.01)
