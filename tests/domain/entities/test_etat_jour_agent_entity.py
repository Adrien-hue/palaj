from datetime import date

import pytest

from core.domain.entities import EtatJourAgent, TypeJour


def test_etat_jour_agent_to_dict_and_from_dict_round_trip():
    etat = EtatJourAgent(agent_id=1, jour=date(2024, 6, 1), type_jour=TypeJour.CONGE, description="Repos bien mérité")

    serialized = etat.to_dict()
    assert serialized == {
        "agent_id": 1,
        "jour": "2024-06-01",
        "type_jour": "conge",
        "description": "Repos bien mérité",
    }

    recreated = EtatJourAgent.from_dict(serialized)
    assert recreated.agent_id == 1
    assert recreated.jour == date(2024, 6, 1)
    assert recreated.type_jour is TypeJour.CONGE
    assert recreated.description == "Repos bien mérité"


def test_etat_jour_agent_invalid_type_raises_value_error():
    with pytest.raises(ValueError):
        EtatJourAgent.from_dict({"agent_id": 2, "jour": "2024-01-01", "type_jour": "invalide"})


def test_etat_jour_agent_str_and_setter():
    etat = EtatJourAgent(agent_id=3, jour=date(2024, 12, 24), type_jour=TypeJour.REPOS)
    etat.set_agent("AGENT") # pyright: ignore[reportArgumentType]

    text = str(etat)
    assert etat.agent == "AGENT"
    assert "2024-12-24" in text
    assert "repos" in text.lower()
    assert "<EtatJourAgent 3" in etat.__repr__()