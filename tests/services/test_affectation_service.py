import pytest
from datetime import date
from core.domain.entities import Agent, Tranche, Affectation
from core.domain.entities.etat_jour_agent import EtatJourAgent, TypeJour
from core.domain.services.affectation_service import AffectationService
from core.utils.domain_alert import Severity


# -------------------------------------------------------------------
# 🔧 Fixtures de mocks simples
# -------------------------------------------------------------------

@pytest.fixture
def mock_agent_repo(mocker):
    repo = mocker.Mock()
    repo.get.side_effect = lambda _id: Agent(id=_id, nom="Dupont", prenom="Jean") if _id == 1 else None
    return repo


@pytest.fixture
def mock_tranche_repo(mocker):
    repo = mocker.Mock()
    repo.get.side_effect = lambda _id: Tranche(id=_id, abbr="MJ", debut="08:00", fin="16:00") if _id == 10 else None
    return repo


@pytest.fixture
def mock_etat_repo(mocker):
    repo = mocker.Mock()
    repo.list_for_agent.return_value = []
    return repo


@pytest.fixture
def mock_affect_repo(mocker):
    repo = mocker.Mock()
    repo.list_for_agent.return_value = []
    repo.create = mocker.Mock()
    repo.list_all.return_value = []
    repo.get.side_effect = lambda _id: None
    return repo


@pytest.fixture
def service(mock_agent_repo, mock_affect_repo, mock_etat_repo, mock_tranche_repo):
    return AffectationService(
        agent_repo=mock_agent_repo,
        affectation_repo=mock_affect_repo,
        etat_jour_agent_repo=mock_etat_repo,
        tranche_repo=mock_tranche_repo,
        verbose=False
    )


# -------------------------------------------------------------------
# 1️⃣ Tests de base sur can_assign
# -------------------------------------------------------------------

def test_can_assign_ok(service, mock_affect_repo, mock_etat_repo):
    agent = Agent(id=1, nom="Dupont", prenom="Jean")
    tranche = Tranche(id=10, abbr="MJ", debut="08:00", fin="16:00")
    jour = date(2025, 1, 1)

    mock_affect_repo.list_for_agent.return_value = []
    mock_etat_repo.list_for_agent.return_value = []

    ok, alerts = service.can_assign(agent, tranche, jour)
    assert ok is True
    assert alerts == []


def test_can_assign_agent_en_repos(service, mock_etat_repo):
    agent = Agent(id=1, nom="Dupont", prenom="Jean")
    tranche = Tranche(id=10, abbr="MJ", debut="08:00", fin="16:00")
    jour = date(2025, 1, 1)

    mock_etat_repo.list_for_agent.return_value = [
        EtatJourAgent(agent_id=1, jour=jour, type_jour=TypeJour.REPOS)
    ]

    ok, alerts = service.can_assign(agent, tranche, jour)

    assert not ok
    assert any("repos" in a.message.lower() for a in alerts)


def test_can_assign_deja_affecte(service, mock_affect_repo):
    agent = Agent(id=1, nom="Dupont", prenom="Jean")
    tranche = Tranche(id=10, abbr="MJ", debut="08:00", fin="16:00")
    jour = date(2025, 1, 1)

    mock_affect_repo.list_for_agent.return_value = [
        Affectation(agent.id, tranche.id, jour)
    ]

    ok, alerts = service.can_assign(agent, tranche, jour)
    assert not ok
    assert any("déjà affecté" in a.message for a in alerts)


def test_can_assign_invalid_params(service):
    ok, alerts = service.can_assign(None, None, date(2025, 1, 1))
    assert not ok
    assert any("Paramètres invalides" in a.message for a in alerts)


# -------------------------------------------------------------------
# 2️⃣ Tests sur create_affectation
# -------------------------------------------------------------------

def test_create_affectation_simulation_ok(service, mock_affect_repo):
    agent = Agent(id=1, nom="Dupont", prenom="Jean")
    tranche = Tranche(id=10, abbr="MJ", debut="08:00", fin="16:00")
    jour = date(2025, 1, 1)

    mock_affect_repo.list_for_agent.return_value = []

    ok, affect, alerts = service.create_affectation(agent, tranche, jour, simulate=True)
    assert ok is True
    assert isinstance(affect, Affectation)
    assert alerts == []


def test_create_affectation_real_creation_error(service, mock_affect_repo):
    agent = Agent(id=1, nom="Dupont", prenom="Jean")
    tranche = Tranche(id=10, abbr="MJ", debut="08:00", fin="16:00")
    jour = date(2025, 1, 1)

    mock_affect_repo.list_for_agent.return_value = []
    mock_affect_repo.create.side_effect = Exception("DB failure")

    ok, affect, alerts = service.create_affectation(agent, tranche, jour, simulate=False)
    assert not ok
    assert affect is None
    assert any("Erreur" in a.message for a in alerts)


def test_create_affectation_invalid_due_to_repos(service, mock_etat_repo):
    agent = Agent(id=1, nom="Dupont", prenom="Jean")
    tranche = Tranche(id=10, abbr="MJ", debut="08:00", fin="16:00")
    jour = date(2025, 1, 1)

    mock_etat_repo.list_for_agent.return_value = [
        EtatJourAgent(agent.id, jour, TypeJour.REPOS)
    ]

    ok, affect, alerts = service.create_affectation(agent, tranche, jour, simulate=True)

    assert not ok
    assert affect is None
    assert any("repos" in a.message.lower() for a in alerts)


# -------------------------------------------------------------------
# 3️⃣ Vérifications internes (_check_x)
# -------------------------------------------------------------------

def test_check_agent_and_tranche_missing(service):
    aff = Affectation(agent_id=None, tranche_id=None, jour=date(2025, 1, 1))
    alerts = service._check_agent(aff)
    alerts += service._check_tranche(aff)
    assert any("non spécifié" in a.message for a in alerts)


def test_check_agent_not_found(service, mock_agent_repo):
    aff = Affectation(agent_id=99, tranche_id=10, jour=date(2025, 1, 1))
    alerts = service._check_agent(aff)
    assert any("introuvable" in a.message for a in alerts)


def test_check_tranche_not_found(service, mock_tranche_repo):
    aff = Affectation(agent_id=1, tranche_id=99, jour=date(2025, 1, 1))
    alerts = service._check_tranche(aff)
    assert any("Tranche introuvable" in a.message for a in alerts)


def test_check_etat_jour_incoherent(service, mock_etat_repo):
    aff = Affectation(agent_id=1, tranche_id=10, jour=date(2025, 1, 1))
    mock_etat_repo.list_for_agent.return_value = [
        EtatJourAgent(1, date(2025, 1, 1), TypeJour.REPOS)
    ]
    alerts = service._check_etat_jour(aff)
    assert any("incohérente" in a.message for a in alerts)
    assert alerts[0].severity == Severity.WARNING


def test_check_doublons_detecte(service):
    jour = date(2025, 1, 1)
    a1 = Affectation(agent_id=1, tranche_id=10, jour=jour)
    a2 = Affectation(agent_id=1, tranche_id=11, jour=jour)
    alerts = service._check_doublons([a1, a2])
    assert any("Doublon" in a.message for a in alerts)


# -------------------------------------------------------------------
# 4️⃣ Validation globale
# -------------------------------------------------------------------

def test_validate_ok(service):
    aff = Affectation(agent_id=1, tranche_id=10, jour=date(2025, 1, 1))
    ok, alerts = service.validate(aff)
    assert ok is True
    assert alerts == []


def test_validate_affectation_invalide(service):
    ok, alerts = service.validate(None)
    assert not ok
    assert any("Affectation vide" in a.message for a in alerts)


def test_validate_by_id_not_found(service, mock_affect_repo):
    mock_affect_repo.get.return_value = None
    ok, alerts = service.validate_by_id("inconnue")
    assert not ok
    assert any("Affectation vide" in a.message for a in alerts)


def test_validate_all_with_doublons(service, mock_affect_repo, mock_tranche_repo):
    jour = date(2025, 1, 1)
    a1 = Affectation(agent_id=1, tranche_id=10, jour=jour)
    a2 = Affectation(agent_id=1, tranche_id=11, jour=jour)
    mock_affect_repo.list_all.return_value = [a1, a2]

    # 👉 Corrige ici : on fait croire que toutes les tranches existent
    mock_tranche_repo.get.side_effect = lambda _id: Tranche(id=_id, abbr=f"T{_id}", debut="08:00", fin="16:00")

    ok, alerts = service.validate_all()
    print("[DEBUG] ok:", ok)
    print("[DEBUG] alerts:", alerts)
    assert not ok
    assert any("doublon" in a.message.lower() for a in alerts)

