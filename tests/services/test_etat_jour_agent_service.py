import pytest
from datetime import date
from core.domain.entities import Agent, EtatJourAgent, TypeJour
from core.domain.services.etat_jour_agent_service import EtatJourAgentService
from core.utils.domain_alert import Severity


@pytest.fixture
def mock_repos(mocker):
    etat_repo = mocker.Mock()
    aff_repo = mocker.Mock()
    agent_repo = mocker.Mock()

    # 👇 Définit des retours sûrs par défaut pour éviter le TypeError
    etat_repo.list_for_agent.return_value = []
    etat_repo.list_all.return_value = []
    aff_repo.list_for_agent.return_value = []
    agent_repo.get.return_value = None

    return etat_repo, aff_repo, agent_repo



@pytest.fixture
def service(mock_repos):
    etat_repo, aff_repo, agent_repo = mock_repos
    return EtatJourAgentService(
        etat_jour_agent_repo=etat_repo,
        affectation_repo=aff_repo,
        agent_repo=agent_repo,
        verbose=False,
    )


@pytest.fixture
def agent():
    return Agent(id=1, nom="Dupont", prenom="Jean")


# -------------------------------------------------------------------
# 1️⃣ can_add_state
# -------------------------------------------------------------------

def test_can_add_state_ok(service, mock_repos, agent):
    etat_repo, _, _ = mock_repos
    etat_repo.list_for_agent.return_value = []
    ok, alerts = service.can_add_state(agent, date(2025, 1, 1))
    assert ok is True
    assert alerts == []


def test_can_add_state_doublon(service, mock_repos, agent):
    jour = date(2025, 1, 1)
    existing = [EtatJourAgent(agent.id, jour, TypeJour.REPOS)]
    etat_repo, _, _ = mock_repos
    etat_repo.list_for_agent.return_value = existing

    ok, alerts = service.can_add_state(agent, jour)
    assert ok is False
    assert any("déjà un état" in a.message.lower() for a in alerts)


# -------------------------------------------------------------------
# 2️⃣ create_state
# -------------------------------------------------------------------

def test_create_state_ok(service, mock_repos, agent):
    etat_repo, aff_repo, _ = mock_repos
    etat_repo.list_for_agent.return_value = []
    aff_repo.list_for_agent.return_value = []

    ok, etat, alerts = service.create_state(agent, date(2025, 1, 1), TypeJour.REPOS)
    assert ok is True
    assert isinstance(etat, EtatJourAgent)
    assert etat.type_jour == TypeJour.REPOS
    assert alerts == []


def test_create_state_type_invalide(service, mock_repos, agent):
    ok, etat, alerts = service.create_state(agent, date(2025, 1, 1), "invalide")
    assert ok is False
    assert etat is None
    assert any("invalide" in a.message.lower() for a in alerts)


def test_create_state_doublon(service, mock_repos, agent):
    jour = date(2025, 1, 1)
    existing = [EtatJourAgent(agent.id, jour, TypeJour.REPOS)]
    etat_repo, aff_repo, _ = mock_repos
    etat_repo.list_for_agent.return_value = existing
    aff_repo.list_for_agent.return_value = []

    ok, etat, alerts = service.create_state(agent, jour, TypeJour.REPOS)
    assert not ok
    assert etat is None
    assert any("déjà un état" in a.message.lower() for a in alerts)


def test_create_state_conflit_avec_affectation(service, mock_repos, agent):
    jour = date(2025, 1, 1)
    etat_repo, aff_repo, _ = mock_repos
    etat_repo.list_for_agent.return_value = []
    # Affectation existante le même jour
    affectation = type("Affectation", (), {"jour": jour})
    aff_repo.list_for_agent.return_value = [affectation]

    ok, etat, alerts = service.create_state(agent, jour, TypeJour.REPOS)
    assert ok  # WARNING, mais pas bloquant
    assert any(a.severity == Severity.WARNING for a in alerts)
    assert any("incohérence" in a.message.lower() for a in alerts)


# -------------------------------------------------------------------
# 3️⃣ ensure_poste_state
# -------------------------------------------------------------------

def test_ensure_poste_state_auto_create(service, mock_repos, agent):
    jour = date(2025, 1, 1)
    etat_repo, aff_repo, _ = mock_repos
    etat_repo.list_for_agent.return_value = []
    aff_repo.list_for_agent.return_value = []

    ok, etat, alerts = service.ensure_poste_state(agent, jour, simulate=True, auto_create=True)
    assert ok
    assert etat.type_jour == TypeJour.POSTE
    assert alerts == []


def test_ensure_poste_state_pas_auto_create(service, mock_repos, agent):
    jour = date(2025, 1, 1)
    etat_repo, _, _ = mock_repos
    etat_repo.list_for_agent.return_value = []

    ok, etat, alerts = service.ensure_poste_state(agent, jour, auto_create=False)
    assert not ok
    assert etat is None
    assert any("aucun état" in a.message.lower() for a in alerts)


def test_ensure_poste_state_incoherent(service, mock_repos, agent):
    jour = date(2025, 1, 1)
    existing = [EtatJourAgent(agent.id, jour, TypeJour.REPOS)]
    etat_repo, _, _ = mock_repos
    etat_repo.list_for_agent.return_value = existing

    ok, etat, alerts = service.ensure_poste_state(agent, jour)
    assert not ok
    assert any("incohérence" in a.message.lower() for a in alerts)


def test_ensure_poste_state_ok(service, mock_repos, agent):
    jour = date(2025, 1, 1)
    existing = [EtatJourAgent(agent.id, jour, TypeJour.POSTE)]
    etat_repo, _, _ = mock_repos
    etat_repo.list_for_agent.return_value = existing

    ok, etat, alerts = service.ensure_poste_state(agent, jour)
    assert ok
    assert alerts == []


# -------------------------------------------------------------------
# 4️⃣ validate et validate_all
# -------------------------------------------------------------------

def test_validate_agent_inexistant(service, mock_repos):
    etat_repo, _, agent_repo = mock_repos
    agent_repo.get.return_value = None
    etat = EtatJourAgent(agent_id=99, jour=date(2025, 1, 1), type_jour=TypeJour.REPOS)
    ok, alerts = service.validate(etat)
    assert not ok
    assert any("inexistant" in a.message.lower() for a in alerts)


def test_validate_type_inconnu(service, mock_repos):
    etat_repo, _, agent_repo = mock_repos
    agent_repo.get.return_value = True  # agent existant
    etat = EtatJourAgent(agent_id=1, jour=date(2025, 1, 1), type_jour="bidon")  # type invalide
    ok, alerts = service.validate(etat)
    print("[DEBUG] alerts:", alerts)
    assert not ok
    assert any("inconnu" in a.message.lower() for a in alerts)


def test_validate_all_doublons(service, mock_repos):
    jour = date(2025, 1, 1)
    e1 = EtatJourAgent(agent_id=1, jour=jour, type_jour=TypeJour.REPOS)
    e2 = EtatJourAgent(agent_id=1, jour=jour, type_jour=TypeJour.REPOS)
    etat_repo, _, _ = mock_repos
    etat_repo.list_all.return_value = [e1, e2]
    etat_repo.list_for_agent.return_value = [e1, e2]

    ok, alerts = service.validate_all()
    assert not ok
    assert any("doublon" in a.message.lower() for a in alerts)
