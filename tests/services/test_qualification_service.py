import pytest
from core.domain.services.qualification_service import QualificationService
from core.domain.entities import Qualification
from core.utils.domain_alert import Severity


@pytest.fixture
def mock_qualification_repo(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_agent_repo(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_poste_repo(mocker):
    return mocker.Mock()


@pytest.fixture
def service(mock_qualification_repo, mock_agent_repo, mock_poste_repo):
    return QualificationService(
        mock_qualification_repo, mock_agent_repo, mock_poste_repo
    )


# ------------------------------------------------------------------
# 1️⃣ Aucun enregistrement
# ------------------------------------------------------------------
def test_validate_all_empty(service, mock_qualification_repo):
    mock_qualification_repo.list_all.return_value = []

    ok, alerts = service.validate_all()

    assert ok
    assert alerts == []


# ------------------------------------------------------------------
# 2️⃣ Qualification valide (agent et poste existants)
# ------------------------------------------------------------------
def test_validate_all_valid(service, mock_qualification_repo, mock_agent_repo, mock_poste_repo):
    q = Qualification(agent_id=1, poste_id=10)
    mock_qualification_repo.list_all.return_value = [q]

    mock_agent_repo.get.return_value = object()   # agent existe
    mock_poste_repo.get.return_value = object()   # poste existe

    ok, alerts = service.validate_all()

    assert ok
    assert alerts == []
    mock_agent_repo.get.assert_called_once_with(1)
    mock_poste_repo.get.assert_called_once_with(10)


# ------------------------------------------------------------------
# 3️⃣ Qualification avec agent inexistant
# ------------------------------------------------------------------
def test_validate_all_missing_agent(service, mock_qualification_repo, mock_agent_repo, mock_poste_repo):
    q = Qualification(agent_id=999, poste_id=10)
    mock_qualification_repo.list_all.return_value = [q]

    mock_agent_repo.get.return_value = None  # ❌ agent inexistant
    mock_poste_repo.get.return_value = object()

    ok, alerts = service.validate_all()

    assert not ok
    assert len(alerts) == 1
    assert "agent inexistant" in alerts[0].message.lower()
    assert alerts[0].severity == Severity.ERROR
    assert alerts[0].source == "QualificationService"


# ------------------------------------------------------------------
# 4️⃣ Qualification avec poste inexistant
# ------------------------------------------------------------------
def test_validate_all_missing_poste(service, mock_qualification_repo, mock_agent_repo, mock_poste_repo):
    q = Qualification(agent_id=1, poste_id=404)
    mock_qualification_repo.list_all.return_value = [q]

    mock_agent_repo.get.return_value = object()
    mock_poste_repo.get.return_value = None  # ❌ poste inexistant

    ok, alerts = service.validate_all()

    assert not ok
    assert len(alerts) == 1
    assert "poste inexistant" in alerts[0].message.lower()
    assert alerts[0].severity == Severity.ERROR


# ------------------------------------------------------------------
# 5️⃣ Doublon de qualification (même agent + poste)
# ------------------------------------------------------------------
def test_validate_all_duplicate(service, mock_qualification_repo, mock_agent_repo, mock_poste_repo):
    q1 = Qualification(agent_id=1, poste_id=10)
    q2 = Qualification(agent_id=1, poste_id=10)  # ❌ doublon

    mock_qualification_repo.list_all.return_value = [q1, q2]
    mock_agent_repo.get.return_value = object()
    mock_poste_repo.get.return_value = object()

    ok, alerts = service.validate_all()

    # Doublon = WARNING, mais pas bloquant
    assert ok
    assert any("doublon" in a.message.lower() for a in alerts)
    assert any(a.severity == Severity.WARNING for a in alerts)
    assert all(a.source == "QualificationService" for a in alerts)


# ------------------------------------------------------------------
# 6️⃣ Mélange : doublon + références manquantes
# ------------------------------------------------------------------
def test_validate_all_mixed(service, mock_qualification_repo, mock_agent_repo, mock_poste_repo):
    q1 = Qualification(agent_id=1, poste_id=10)
    q2 = Qualification(agent_id=1, poste_id=10)  # doublon
    q3 = Qualification(agent_id=99, poste_id=77)  # agent et poste manquants

    mock_qualification_repo.list_all.return_value = [q1, q2, q3]

    def mock_agent(id):
        return object() if id == 1 else None

    def mock_poste(id):
        return object() if id == 10 else None

    mock_agent_repo.get.side_effect = mock_agent
    mock_poste_repo.get.side_effect = mock_poste

    ok, alerts = service.validate_all()

    # Au moins une erreur (agent/poste manquants)
    assert not ok
    assert any("doublon" in a.message.lower() for a in alerts)
    assert any("inexistant" in a.message.lower() for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)
