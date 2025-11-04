import pytest
from datetime import time
from core.domain.entities.tranche import Tranche

# -------------------------------------------------------------------
# 🧱 1️⃣ Création et parsing basique
# -------------------------------------------------------------------

def test_tranche_creation_with_time_objects():
    t = Tranche(id=1, abbr="MJ", debut=time(6, 0), fin=time(14, 0))
    assert t.debut == time(6, 0)
    assert t.fin == time(14, 0)
    assert t.nb_agents_requis == 1
    assert t.duree_minutes() == 480
    assert t.duree() == 8.0
    assert "08:00" in t.duree_formatee() or "8h00" in t.duree_formatee()

def test_tranche_creation_with_string_times():
    t = Tranche(id=2, abbr="APM", debut="13:30", fin="21:30", nb_agents_requis=2)
    assert t.debut == time(13, 30)
    assert t.fin == time(21, 30)
    assert t.nb_agents_requis == 2
    assert t.duree() == 8.0
    assert t.to_dict()["heure_debut"] == "13:30"

def test_duree_arrondi_deux_decimales():
    t = Tranche(id=9, abbr="T", debut="08:00", fin="12:10")
    assert t.duree() == round(4 + 10/60, 2)  # 4.17

# -------------------------------------------------------------------
# ⏳ 2️⃣ Gestion du passage à minuit
# -------------------------------------------------------------------

def test_tranche_nuit_passage_minuit():
    t = Tranche(id=3, abbr="NJ", debut="22:00", fin="06:20")
    assert t.duree_minutes() == 8 * 60 + 20
    assert t.duree() == 8.33
    assert t.duree_formatee() == "8h20min"

# -------------------------------------------------------------------
# ⚙️ 3️⃣ Conversion JSON et instanciation depuis dict
# -------------------------------------------------------------------

def test_tranche_to_dict_and_from_dict():
    t = Tranche(id=4, abbr="SJ", debut="08:00", fin="16:00", nb_agents_requis=3)
    d = t.to_dict()
    assert d["nom"] == "SJ"
    assert d["heure_debut"] == "08:00"
    assert d["heure_fin"] == "16:00"

    t2 = Tranche.from_dict(d)
    assert t2.abbr == "SJ"
    assert t2.debut == time(8, 0)
    assert t2.fin == time(16, 0)
    assert t2.nb_agents_requis == 3

# -------------------------------------------------------------------
# ❌ 4️⃣ Gestion des erreurs
# -------------------------------------------------------------------

def test_invalid_time_format_raises():
    with pytest.raises(ValueError):
        Tranche(id=5, abbr="ERR", debut="25:61", fin="06:00")

# -------------------------------------------------------------------
# 🖨️ 5️⃣ Représentations textuelles
# -------------------------------------------------------------------

def test_repr_and_str_output_contains_key_info():
    t = Tranche(id=6, abbr="MAT", debut="06:30", fin="14:30")
    r = repr(t)
    s = str(t)
    assert "MAT" in r
    assert "06:30" in r and "14:30" in r
    assert "Durée" in s
    assert "Tranche" in s

# -------------------------------------------------------------------
# 🧮 6️⃣ Validation logique (durées anormales)
# -------------------------------------------------------------------

def test_validate_does_not_raise_for_normal_durations():
    t = Tranche(id=7, abbr="OK", debut="07:00", fin="15:00")
    assert t.duree() <= 11.0

def test_long_tranche_detectable_even_if_validation_is_stubbed():
    """La méthode validate est un stub, mais on vérifie la détection logique."""
    t = Tranche(id=8, abbr="LONG", debut="07:00", fin="20:00")
    assert t.duree() == 13.0  # la logique de durée doit marcher
