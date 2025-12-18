import pytest

from core.domain.entities import Regime

def test_regime_to_dict_and_from_dict_round_trip():
    source = {
        "id": 2,
        "nom": "R2",
        "desc": "Temps plein",
        "duree_moyenne_journee_service_min": 480,
        "repos_periodiques_annuels": 12,
    }

    regime = Regime.from_dict(source)
    assert regime.id == 2
    assert regime.nom == "R2"
    assert regime.desc == "Temps plein"
    assert regime.duree_moyenne_journee_service_min == 480
    assert regime.repos_periodiques_annuels == 12
    assert regime.to_dict() == source


def test_regime_string_and_repr_include_duration():
    regime = Regime(id=3, nom="R3", desc="Desc", duree_moyenne_journee_service_min=300, repos_periodiques_annuels=4)

    text = str(regime)
    assert "R3" in text
    assert "5h00" in text  # 300 minutes -> 5h00min
    assert "<Regime id=3" in repr(regime)


def test_regime_sets_agents_collection():
    regime = Regime(id=4, nom="R4")
    regime.set_agents(["A1", "A2"]) # pyright: ignore[reportArgumentType]
    assert regime.agents == ["A1", "A2"]