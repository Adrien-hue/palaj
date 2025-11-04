import pytest
from core.domain.services.regime_service import RegimeService
from core.domain.entities import Regime
from core.utils.domain_alert import Severity


@pytest.fixture
def mock_regime_repo(mocker):
    return mocker.Mock()


@pytest.fixture
def service(mock_regime_repo):
    return RegimeService(mock_regime_repo)


# ------------------------------------------------------------------
# 1️⃣ Aucun régime
# ------------------------------------------------------------------
def test_validate_all_empty(service, mock_regime_repo):
    mock_regime_repo.list_all.return_value = []

    ok, alerts = service.validate_all()

    assert ok
    assert alerts == []


# ------------------------------------------------------------------
# 2️⃣ Régime valide
# ------------------------------------------------------------------
def test_validate_all_valid(service, mock_regime_repo):
    regime = Regime(id=1, nom="RH35H", duree_moyenne_journee_service_min=420)
    mock_regime_repo.list_all.return_value = [regime]

    ok, alerts = service.validate_all()

    assert ok
    assert alerts == []


# ------------------------------------------------------------------
# 3️⃣ Doublon de régime (même ID)
# ------------------------------------------------------------------
def test_validate_all_duplicate_id(service, mock_regime_repo):
    r1 = Regime(id=10, nom="R1", duree_moyenne_journee_service_min=400)
    r2 = Regime(id=10, nom="R2", duree_moyenne_journee_service_min=480)

    mock_regime_repo.list_all.return_value = [r1, r2]

    ok, alerts = service.validate_all()

    assert not ok
    assert len(alerts) == 1
    assert "doublon" in alerts[0].message.lower()
    assert alerts[0].source == "RegimeService"
    assert alerts[0].severity == Severity.ERROR


# ------------------------------------------------------------------
# 4️⃣ Durée moyenne négative — vérifie la levée d’exception au niveau de l’entité
# ------------------------------------------------------------------
def test_regime_entity_raises_on_negative_duration():
    """Vérifie que le constructeur de Regime lève une ValueError si la durée est négative."""
    with pytest.raises(ValueError, match="durée moyenne ne peut pas être négative"):
        Regime(id=5, nom="RH-TEST", duree_moyenne_journee_service_min=-120)


# ------------------------------------------------------------------
# 5️⃣ Cas mixte : doublon + durée négative (simulée via mock)
# ------------------------------------------------------------------
def test_validate_all_mixed(service, mock_regime_repo):
    # On simule un régime "valide" et un régime "fautif"
    valid_regime = Regime(id=1, nom="R1", duree_moyenne_journee_service_min=420)

    # Ici on ne passe pas par le constructeur (pour éviter la ValueError)
    invalid_regime = object.__new__(Regime)
    invalid_regime.id = 1
    invalid_regime.nom = "R1_DUP"
    invalid_regime.duree_moyenne_journee_service_min = -100

    mock_regime_repo.list_all.return_value = [valid_regime, invalid_regime]

    ok, alerts = service.validate_all()

    assert not ok
    assert len(alerts) == 2
    assert any("doublon" in a.message.lower() for a in alerts)
    assert any("négative" in a.message.lower() for a in alerts)
    assert all(a.source == "RegimeService" for a in alerts)
