from datetime import date

import pytest

from core.domain.entities import Affectation


def test_affectation_requires_date_instance():
    with pytest.raises(TypeError):
        Affectation(agent_id=1, tranche_id=2, jour="2024-01-01") # pyright: ignore[reportArgumentType]


def test_affectation_to_dict_and_from_dict_round_trip():
    jour = date(2024, 1, 2)
    affectation = Affectation(agent_id=3, tranche_id=7, jour=jour)

    serialized = affectation.to_dict()
    assert serialized == {
        "agent_id": 3,
        "tranche_id": 7,
        "jour": "2024-01-02",
    }

    recreated = Affectation.from_dict(serialized)
    assert recreated.agent_id == 3
    assert recreated.tranche_id == 7
    assert recreated.jour == jour


def test_affectation_string_and_repr():
    affectation = Affectation(agent_id=5, tranche_id=8, jour=date(2025, 5, 5))

    text = str(affectation)
    assert "Agent ID" in text
    assert "Tranche ID" in text
    assert "2025-05-05" in text
    assert "<Affectation agent=5" in repr(affectation)


def test_affectation_setters_store_links():
    affectation = Affectation(agent_id=9, tranche_id=10, jour=date(2024, 12, 31))

    affectation.set_agent("AGENT") # pyright: ignore[reportArgumentType]
    affectation.set_tranche("TRANCHE") # pyright: ignore[reportArgumentType]

    assert affectation.agent == "AGENT"
    assert affectation.tranche == "TRANCHE"