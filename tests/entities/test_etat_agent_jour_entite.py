import pytest
from datetime import date
from core.domain.entities.etat_jour_agent import EtatJourAgent, TypeJour
from tests.utils.text import strip_ansi


# -------------------------------------------------------------------
# 1️⃣ Création et attributs de base
# -------------------------------------------------------------------

def test_etat_jour_agent_creation_and_id():
    e = EtatJourAgent(agent_id=5, jour=date(2025, 1, 10), type_jour=TypeJour.POSTE, description="Service matin")
    assert e.agent_id == 5
    assert e.jour == date(2025, 1, 10)
    assert e.type_jour == TypeJour.POSTE
    assert e.description == "Service matin"
    assert e.id == "5_20250110"
    assert "POSTE" in repr(e)
    assert "2025-01-10" in repr(e)


def test_etat_jour_agent_default_description():
    e = EtatJourAgent(2, date(2025, 2, 2), TypeJour.REPOS)
    assert e.description == ""


def test_equality_and_hash():
    j = date(2025, 1, 10)
    e1 = EtatJourAgent(1, j, TypeJour.ZCOT)
    e2 = EtatJourAgent(1, j, TypeJour.ZCOT)
    e3 = EtatJourAgent(2, j, TypeJour.ZCOT)

    assert e1 == e2
    assert e1 != e3
    assert hash(e1) == hash(e2)
    assert len({e1, e2, e3}) == 2  # les doublons sont filtrés


# -------------------------------------------------------------------
# 2️⃣ Affichage
# -------------------------------------------------------------------

def test_str_representation_contains_all_fields():
    e = EtatJourAgent(7, date(2025, 1, 15), TypeJour.ABSENCE, "Maladie")
    s = strip_ansi(str(e))
    assert "Agent ID:" in s
    assert "Jour:" in s
    assert "Type:" in s

def test_str_representation_with_empty_description():
    e = EtatJourAgent(9, date(2025, 1, 15), TypeJour.REPOS)
    s = strip_ansi(str(e))
    assert "—" in s or "Aucune" not in s  # symbole de vide bien affiché


# -------------------------------------------------------------------
# 3️⃣ JSON Helpers
# -------------------------------------------------------------------

def test_to_dict_and_from_dict_are_inverse():
    e = EtatJourAgent(10, date(2025, 3, 10), TypeJour.ZCOT, "Présence site")
    d = e.to_dict()
    assert d == {
        "agent_id": 10,
        "jour": "2025-03-10",
        "type_jour": "zcot",
        "description": "Présence site",
    }

    clone = EtatJourAgent.from_dict(d)
    assert clone.agent_id == 10
    assert clone.jour == date(2025, 3, 10)
    assert clone.type_jour == TypeJour.ZCOT
    assert clone.description == "Présence site"
    assert clone == e


def test_from_dict_invalid_type_raises():
    bad_data = {"agent_id": 1, "jour": "2025-01-01", "type_jour": "invalid_type"}
    with pytest.raises(ValueError):
        EtatJourAgent.from_dict(bad_data)


# -------------------------------------------------------------------
# 4️⃣ Enum TypeJour
# -------------------------------------------------------------------

def test_type_jour_enum_values():
    assert TypeJour.POSTE.value == "poste"
    assert TypeJour.ZCOT.value == "zcot"
    assert TypeJour.REPOS.value == "repos"
    assert TypeJour.CONGE.value == "conge"
    assert TypeJour.ABSENCE.value == "absence"
