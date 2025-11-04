import pytest

from core.domain.entities.regime import Regime

from tests.utils.text import strip_ansi
# -------------------------------------------------------------------
# 🧱 1️⃣ Création et affichage basique
# -------------------------------------------------------------------

def test_regime_creation_and_basic_properties():
    r = Regime(
        id=1,
        nom="RH-Q",
        desc="Régime des agents de conduite",
        duree_moyenne_journee_service_min=420,
        repos_periodiques_annuels=96,
    )

    assert r.id == 1
    assert r.nom == "RH-Q"
    assert r.desc.startswith("Régime")
    assert r.duree_moyenne_journee_service_min == 420
    assert r.repos_periodiques_annuels == 96

def test_regime_str_and_repr_contain_key_info():
    r = Regime(2, "RH-T", desc="Travailleur de jour", duree_moyenne_journee_service_min=450, repos_periodiques_annuels=104)
    s = str(r)
    r_str = repr(r)

    # __str__ avec couleurs ANSI et libellés lisibles
    assert "Régime" in s
    assert "RH-T" in s
    assert "Durée moyenne journée" in s
    assert "Repos périodiques" in s

    # __repr__ résumé technique
    assert "<Regime" in r_str
    assert "7h30min" in r_str  # 450 min = 7h30

def test_regime_negative_duration_raises():
    with pytest.raises(ValueError):
        Regime(7, "ERR", duree_moyenne_journee_service_min=-60)

# -------------------------------------------------------------------
# ⚙️ 2️⃣ Conversion dictionnaire / reconstruction
# -------------------------------------------------------------------

def test_to_dict_and_from_dict_are_inverse():
    base = Regime(
        id=3,
        nom="RH-N",
        desc="Régime de nuit",
        duree_moyenne_journee_service_min=480,
        repos_periodiques_annuels=80,
    )
    data = base.to_dict()
    assert data == {
        "id": 3,
        "nom": "RH-N",
        "desc": "Régime de nuit",
        "duree_moyenne_journee_service_min": 480,
        "repos_periodiques_annuels": 80,
    }

    clone = Regime.from_dict(data)
    assert clone.id == 3
    assert clone.nom == "RH-N"
    assert clone.duree_moyenne_journee_service_min == 480
    assert clone.repos_periodiques_annuels == 80
    assert clone.desc == "Régime de nuit"

def test_from_dict_with_missing_optional_fields():
    data = {"id": 4, "nom": "RH-A"}
    r = Regime.from_dict(data)
    assert r.desc == ""
    assert r.duree_moyenne_journee_service_min == 0
    assert r.repos_periodiques_annuels == 0

# -------------------------------------------------------------------
# 🧩 3️⃣ Robustesse et valeurs limites
# -------------------------------------------------------------------

def test_regime_zero_duration_and_zero_repos():
    r = Regime(5, "RH-Z", duree_moyenne_journee_service_min=0, repos_periodiques_annuels=0)
    s = strip_ansi(str(r))
    assert "Durée moyenne journée" in s
    assert "Inconnue" in s
    assert "Repos périodiques annuels:" in s
    assert s.split("Repos périodiques annuels:")[-1].strip().startswith("0")
