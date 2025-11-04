import pytest
from core.domain.entities.poste import Poste
from core.domain.entities.tranche import Tranche
from tests.utils.text import strip_ansi

# -------------------------------------------------------------------
# 🧱 1️⃣ Création et représentation basique
# -------------------------------------------------------------------

def test_poste_creation_and_basic_properties():
    p = Poste(id=1, nom="GMJ", tranche_ids=[10, 11])
    assert p.id == 1
    assert p.nom == "GMJ"
    assert p.tranche_ids == [10, 11]
    assert p._tranches is None
    assert p._qualifications is None
    assert repr(p) == "<Poste GMJ: 2 tranches>"

def test_poste_str_contains_all_key_info():
    p = Poste(2, "RLIVM7P", tranche_ids=[1, 2, 3])
    s = strip_ansi(str(p))
    assert "Poste RLIVM7P" in s
    assert "Tranches ids" in s
    assert "[1, 2, 3]" in s
    assert "Non chargé" in s  # lazy loading non encore exécuté

# -------------------------------------------------------------------
# ⚙️ 2️⃣ Lazy loading des tranches
# -------------------------------------------------------------------

class DummyTrancheRepo:
    """Simule un dépôt de tranches en mémoire."""
    def __init__(self):
        self.data = {
            1: Tranche(1, "MJ", "06:00", "14:00"),
            2: Tranche(2, "SJ", "14:00", "22:00"),
            3: Tranche(3, "NJ", "22:00", "06:00"),
        }

    def get(self, id_):
        return self.data.get(id_)

def test_get_tranches_loads_and_caches_results():
    repo = DummyTrancheRepo()
    poste = Poste(3, "RHQ", tranche_ids=[1, 2])

    tranches = poste.get_tranches(repo)
    assert len(tranches) == 2
    assert all(isinstance(t, Tranche) for t in tranches)
    # ⚡ Lazy loading : doit être stocké
    assert poste._tranches is tranches
    # ⚡ Deuxième appel : pas de nouvel accès au repo
    repo.data.clear()
    assert poste.get_tranches(repo) == tranches

def test_get_tranches_with_missing_ids_ignores_none():
    class EmptyRepo:
        def get(self, id_): return None

    p = Poste(4, "TST", tranche_ids=[999])
    result = p.get_tranches(EmptyRepo())
    assert result == []
    assert p._tranches == []

# -------------------------------------------------------------------
# 🧩 3️⃣ Lazy loading des qualifications
# -------------------------------------------------------------------

class DummyQualificationRepo:
    def list_for_poste(self, poste_id):
        return [{"id": 1, "nom": "COND"}] if poste_id == 5 else []

def test_get_qualifications_loads_and_caches_results():
    repo = DummyQualificationRepo()
    poste = Poste(5, "RLIV", tranche_ids=[])
    result = poste.get_qualifications(repo)
    assert isinstance(result, list)
    assert result == [{"id": 1, "nom": "COND"}]
    # ⚡ Caching
    assert poste._qualifications == result
    repo.data = "not_used"
    assert poste.get_qualifications(repo) == result  # cached

# -------------------------------------------------------------------
# 📤 4️⃣ Conversion dictionnaire
# -------------------------------------------------------------------

def test_poste_to_dict_and_from_dict_are_inverse():
    base = Poste(id=6, nom="GMN", tranche_ids=[10, 20])
    data = base.to_dict()
    assert data == {"id": 6, "nom": "GMN", "tranches": [10, 20]}

    clone = Poste.from_dict(data)
    assert clone.id == 6
    assert clone.nom == "GMN"
    assert clone.tranche_ids == [10, 20]
    assert isinstance(clone, Poste)

# -------------------------------------------------------------------
# 🔍 5️⃣ Robustesse - valeurs vides
# -------------------------------------------------------------------

def test_poste_creation_with_no_tranches():
    p = Poste(id=7, nom="RLIVS")
    assert p.tranche_ids == []
    assert "0 tranches" in repr(p)

def test_poste_str_without_tranches_and_qualifications():
    p = Poste(8, "GMJ")
    s = strip_ansi(str(p))
    assert "Non chargé" in s
    assert "Tranches ids: []" in s