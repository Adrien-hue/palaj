from datetime import date
from core.domain.entities.qualification import Qualification
from tests.utils.text import strip_ansi

# -------------------------------------------------------------------
# 1️⃣ Création basique & identifiant composite
# -------------------------------------------------------------------

def test_qualification_creation_and_id():
    q = Qualification(agent_id=1, poste_id=2, date_qualification=date(2025, 1, 10))
    assert q.agent_id == 1
    assert q.poste_id == 2
    assert q.date_qualification == date(2025, 1, 10)
    assert q.id == "1_2"
    assert "1" in repr(q)
    assert "2" in repr(q)

def test_qualification_without_date():
    q = Qualification(agent_id=5, poste_id=9)
    assert q.date_qualification is None
    assert q.id == "5_9"
    assert "?" in repr(q)

def test_str_representation():
    q = Qualification(3, 8)
    s = str(q)
    assert "agent=3" in s and "poste=8" in s

# -------------------------------------------------------------------
# 2️⃣ Lazy loading des entités liées
# -------------------------------------------------------------------

class DummyAgentRepo:
    def __init__(self):
        self.get_calls = []
    def get(self, id_):
        self.get_calls.append(id_)
        return {"id": id_, "nom": f"Agent-{id_}"}

class DummyPosteRepo:
    def __init__(self):
        self.get_calls = []
    def get(self, id_):
        self.get_calls.append(id_)
        return {"id": id_, "nom": f"Poste-{id_}"}

def test_get_agent_and_poste_loads_once():
    q = Qualification(7, 3)
    agent_repo = DummyAgentRepo()
    poste_repo = DummyPosteRepo()

    a1 = q.get_agent(agent_repo)
    p1 = q.get_poste(poste_repo)

    # Retourne les valeurs correctes
    assert a1 == {"id": 7, "nom": "Agent-7"}
    assert p1 == {"id": 3, "nom": "Poste-3"}

    # Lazy loading : doit être mis en cache
    assert q._agent == a1
    assert q._poste == p1

    # Deuxième appel → aucune requête supplémentaire
    agent_repo.get_calls.clear()
    poste_repo.get_calls.clear()
    q.get_agent(agent_repo)
    q.get_poste(poste_repo)
    assert not agent_repo.get_calls
    assert not poste_repo.get_calls

# -------------------------------------------------------------------
# 3️⃣ Sérialisation / Désérialisation
# -------------------------------------------------------------------

def test_to_dict_and_from_dict_with_date():
    d = date(2025, 1, 10)
    q = Qualification(10, 20, d)
    data = q.to_dict()
    assert data == {
        "agent_id": 10,
        "poste_id": 20,
        "date_qualification": "2025-01-10",
    }

    clone = Qualification.from_dict(data)
    assert clone.agent_id == 10
    assert clone.poste_id == 20
    assert clone.date_qualification == d

def test_from_dict_without_date():
    data = {"agent_id": 1, "poste_id": 2, "date_qualification": None}
    q = Qualification.from_dict(data)
    assert q.date_qualification is None
    assert q.id == "1_2"
