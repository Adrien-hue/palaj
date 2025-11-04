import pytest
from core.domain.entities.agent import Agent
from core.domain.services.agent_service import AgentService
from core.utils.domain_alert import Severity


@pytest.fixture
def mock_agent_repo(mocker):
    repo = mocker.Mock()
    repo.list_all.return_value = []
    return repo


@pytest.fixture
def service(mock_agent_repo):
    return AgentService(agent_repo=mock_agent_repo)


# -------------------------------------------------------------------
# 1️⃣ Tests unitaires sur validate()
# -------------------------------------------------------------------

def test_validate_agent_valide(service):
    """✅ Cas nominal : agent complet, sans erreur ni alerte"""
    agent = Agent(id=1, nom="Dupont", prenom="Jean")
    ok, alerts = service.validate(agent)
    assert ok is True
    assert alerts == []


def test_validate_agent_sans_nom(service):
    """⚠️ Agent sans nom → alerte WARNING"""
    agent = Agent(id=1, nom="", prenom="Jean")
    ok, alerts = service.validate(agent)
    assert ok is True  # pas d'erreur bloquante
    assert any(a.severity == Severity.WARNING for a in alerts)
    assert any("sans nom" in a.message for a in alerts)


def test_validate_agent_sans_prenom(service):
    """⚠️ Agent sans prénom → alerte WARNING"""
    agent = Agent(id=1, nom="Dupont", prenom="")
    ok, alerts = service.validate(agent)
    assert ok is True
    assert any("sans nom ou prénom" in a.message.lower() for a in alerts)


def test_validate_agent_sans_id(service):
    """🚨 Agent sans identifiant → erreur ERROR"""
    agent = Agent(id=None, nom="Dupont", prenom="Jean")
    ok, alerts = service.validate(agent)
    assert ok is False
    assert any(a.severity == Severity.ERROR for a in alerts)
    assert any("sans identifiant" in a.message.lower() for a in alerts)


def test_validate_agent_sans_id_et_nom(service):
    """🚨 Agent sans id et sans nom → 1 erreur + 1 warning"""
    agent = Agent(id=None, nom="", prenom="")
    ok, alerts = service.validate(agent)
    assert ok is False  # une erreur est bloquante
    assert any(a.severity == Severity.ERROR for a in alerts)
    assert any(a.severity == Severity.WARNING for a in alerts)


# -------------------------------------------------------------------
# 2️⃣ Tests sur validate_all()
# -------------------------------------------------------------------

def test_validate_all_ok(service, mock_agent_repo):
    """✅ Tous les agents valides"""
    agents = [
        Agent(id=1, nom="Dupont", prenom="Jean"),
        Agent(id=2, nom="Martin", prenom="Sophie"),
    ]
    mock_agent_repo.list_all.return_value = agents

    ok, alerts = service.validate_all()
    assert ok is True
    assert alerts == []


def test_validate_all_doublon_id(service, mock_agent_repo):
    """🚨 Deux agents avec le même ID"""
    agents = [
        Agent(id=1, nom="Dupont", prenom="Jean"),
        Agent(id=1, nom="Martin", prenom="Sophie"),  # doublon
    ]
    mock_agent_repo.list_all.return_value = agents

    ok, alerts = service.validate_all()
    assert ok is False
    assert any("doublon" in a.message.lower() for a in alerts)


def test_validate_all_melange_erreur_warning(service, mock_agent_repo):
    """⚠️ Mélange de WARNING (nom manquant) et ERROR (id manquant)"""
    agents = [
        Agent(id=1, nom="", prenom="Jean"),          # warning
        Agent(id=None, nom="Martin", prenom="Sophie")  # erreur
    ]
    mock_agent_repo.list_all.return_value = agents

    ok, alerts = service.validate_all()
    assert ok is False
    assert any(a.severity == Severity.ERROR for a in alerts)
    assert any(a.severity == Severity.WARNING for a in alerts)
