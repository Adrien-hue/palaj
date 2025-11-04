import pytest
from datetime import date
from core.domain.entities.affectation import Affectation
from tests.utils.text import strip_ansi


# -------------------------------------------------------------------
# 1️⃣ Création & validation de base
# -------------------------------------------------------------------

def test_affectation_creation_and_id():
    jour = date(2025, 1, 20)
    a = Affectation(agent_id=1, tranche_id=2, jour=jour)

    assert a.agent_id == 1
    assert a.tranche_id == 2
    assert a.jour == jour
    assert a.id == "1_20250120_2"
    assert "Affectation" in repr(a)

def test_affectation_invalid_date_type_raises():
    with pytest.raises(TypeError):
        Affectation(agent_id=1, tranche_id=2, jour="2025-01-20")

def test_affectation_equality_and_hash():
    j = date(2025, 1, 10)
    a1 = Affectation(1, 2, j)
    a2 = Affectation(1, 2, j)
    a3 = Affectation(2, 2, j)

    assert a1 == a2
    assert a1 != a3
    assert hash(a1) == hash(a2)
    assert len({a1, a2, a3}) == 2  # set doit éliminer les doublons

def test_affectation_str_contains_all_data():
    a = Affectation(3, 4, date(2025, 1, 10))
    s = strip_ansi(str(a))
    assert "Agent ID:" in s
    assert "Tranche ID:" in s
    assert "Jour:" in s
    assert "2025-01-10" in s


# -------------------------------------------------------------------
# 2️⃣ Lazy loading
# -------------------------------------------------------------------

class DummyAgentRepo:
    def __init__(self):
        self.calls = []
    def get(self, id_):
        self.calls.append(id_)
        return {"id": id_, "nom": f"Agent-{id_}"}

class DummyTrancheRepo:
    def __init__(self):
        self.calls = []
    def get(self, id_):
        self.calls.append(id_)
        return {"id": id_, "abbr": f"T-{id_}"}


def test_get_agent_and_tranche_loads_once():
    a = Affectation(10, 20, date(2025, 2, 1))
    agent_repo = DummyAgentRepo()
    tranche_repo = DummyTrancheRepo()

    # Premier appel : charge depuis le repo
    agent = a.get_agent(agent_repo)
    tranche = a.get_tranche(tranche_repo)
    assert agent == {"id": 10, "nom": "Agent-10"}
    assert tranche == {"id": 20, "abbr": "T-20"}
    assert a._agent == agent
    assert a._tranche == tranche

    # Deuxième appel : doit utiliser le cache
    agent_repo.calls.clear()
    tranche_repo.calls.clear()
    a.get_agent(agent_repo)
    a.get_tranche(tranche_repo)
    assert not agent_repo.calls
    assert not tranche_repo.calls


# -------------------------------------------------------------------
# 3️⃣ Sérialisation / Désérialisation
# -------------------------------------------------------------------

def test_to_dict_and_from_dict_are_inverse():
    jour = date(2025, 3, 5)
    a = Affectation(5, 9, jour)
    d = a.to_dict()
    assert d == {"agent_id": 5, "tranche_id": 9, "jour": "2025-03-05"}

    clone = Affectation.from_dict(d)
    assert clone.agent_id == 5
    assert clone.tranche_id == 9
    assert clone.jour == jour
    assert clone == a
