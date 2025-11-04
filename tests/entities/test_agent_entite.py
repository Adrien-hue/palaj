from datetime import date

from unittest.mock import MagicMock

from core.domain.entities import Agent, EtatJourAgent, TypeJour

# Tests unitaires pures
def test_agent_to_dict_and_from_dict():
    data = {
        "id": 1,
        "nom": "Dupont",
        "prenom": "Alice",
        "code_personnel": "A123",
        "regime_id": 5
    }
    agent = Agent.from_dict(data)
    assert agent.nom == "Dupont"
    assert agent.to_dict() == data

def test_agent_str_and_repr():
    a = Agent(1, "Durand", "Bob", "C999")
    s = str(a)
    assert "Bob Durand" in s
    assert "Non chargé" in s  # car lazy fields non initialisés
    assert "<Agent" in repr(a)

def test_get_full_name():
    a = Agent(1, "Martin", "Clara")
    assert a.get_full_name() == "Clara Martin"

# Test avec mock repository
def test_get_regime_lazy_loading():
    mock_repo = MagicMock()
    mock_repo.get.return_value = "REGIME-TEST"

    a = Agent(1, "Dupont", "Alice", regime_id=42)
    result = a.get_regime(mock_repo)
    
    assert result == "REGIME-TEST"
    mock_repo.get.assert_called_once_with(42)

def test_get_qualifications_lazy_loading():
    mock_repo = MagicMock()
    mock_repo.list_for_agent.return_value = ["ADC", "MEC"]

    a = Agent(1, "Durand", "Paul")
    result = a.get_qualifications(mock_repo)

    assert result == ["ADC", "MEC"]
    mock_repo.list_for_agent.assert_called_once_with(1)

def test_get_repos_jours_lazy_loading():
    mock_repo = MagicMock()
    mock_repo.list_repos_for_agent.return_value = ["J1", "J2"]

    a = Agent(1, "Martin", "Clara")
    result = a.get_repos_jours(mock_repo)

    assert result == ["J1", "J2"]
    mock_repo.list_repos_for_agent.assert_called_once_with(1)

# Test d'intégration légère
def test_agent_with_loaded_states():
    agent = Agent(1, "Dupont", "Alice")

    agent._repos_jours = [
        EtatJourAgent(agent_id=1, jour=date(2025, 1, 1), type_jour=TypeJour.REPOS),
        EtatJourAgent(agent_id=1, jour=date(2025, 1, 2), type_jour=TypeJour.REPOS),
    ]

    agent._zcot_jours = [
        EtatJourAgent(agent_id=1, jour=date(2025, 1, 3), type_jour=TypeJour.ZCOT)
    ]

    assert len(agent._repos_jours) == 2
    assert len(agent._zcot_jours) == 1
    assert "Repos" in str(agent)