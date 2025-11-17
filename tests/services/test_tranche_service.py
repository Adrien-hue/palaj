import pytest
from datetime import time
from core.domain.services.tranche_validator_service import TrancheService
from core.domain.entities import Tranche
from core.utils.domain_alert import Severity


@pytest.fixture
def mock_tranche_repo(mocker):
    return mocker.Mock()


@pytest.fixture
def service(mock_tranche_repo):
    return TrancheService(mock_tranche_repo)


# ------------------------------------------------------------------
# 1️⃣ Aucune tranche
# ------------------------------------------------------------------
def test_validate_all_empty(service, mock_tranche_repo):
    mock_tranche_repo.list_all.return_value = []
    ok, alerts = service.validate_all()
    assert ok
    assert alerts == []


# ------------------------------------------------------------------
# 2️⃣ Tranche valide
# ------------------------------------------------------------------
def test_validate_all_valid(service, mock_tranche_repo):
    t = Tranche(id=1, nom="MJ", heure_debut="08:00", heure_fin="16:00", poste_id=9999)
    mock_tranche_repo.list_all.return_value = [t]

    ok, alerts = service.validate_all()
    assert ok
    assert alerts == []


# ------------------------------------------------------------------
# 3️⃣ Doublon d’ID
# ------------------------------------------------------------------
def test_validate_all_duplicate(service, mock_tranche_repo):
    t1 = Tranche(id=1, nom="MJ1", heure_debut="07:00", heure_fin="15:00", poste_id=9999)
    t2 = Tranche(id=1, nom="MJ2", heure_debut="09:00", heure_fin="17:00", poste_id=9999)
    mock_tranche_repo.list_all.return_value = [t1, t2]

    ok, alerts = service.validate_all()
    assert not ok
    assert any("doublon" in a.message.lower() for a in alerts)
    assert all(a.source == "TrancheService" for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)


# ------------------------------------------------------------------
# 4️⃣ Horaire manquant (début ou fin absent)
# ------------------------------------------------------------------
def test_validate_all_missing_times(service, mock_tranche_repo):
    t1 = Tranche(id=1, nom="INCOMPLETE", heure_debut="", heure_fin="12:00", poste_id=9999)
    t2 = Tranche(id=2, nom="INCOMPLETE2", heure_debut="08:00", heure_fin="", poste_id=9999)
    mock_tranche_repo.list_all.return_value = [t1, t2]

    ok, alerts = service.validate_all()
    assert not ok
    assert len(alerts) == 2
    assert all("horaires incomplets" in a.message.lower() for a in alerts)


# ------------------------------------------------------------------
# 5️⃣ Durée nulle
# ------------------------------------------------------------------
def test_validate_all_zero_duration(service, mock_tranche_repo):
    t = Tranche(id=1, nom="ZERO", heure_debut="08:00", heure_fin="08:00", poste_id=9999)
    mock_tranche_repo.list_all.return_value = [t]

    ok, alerts = service.validate_all()
    assert not ok
    assert any("durée nulle" in a.message.lower() for a in alerts)


# ------------------------------------------------------------------
# 6️⃣ Durée > 24h (impossible)
# ------------------------------------------------------------------
def test_validate_all_duration_over_24h(service, mock_tranche_repo):
    t = Tranche(id=1, nom="LONGUE", heure_debut="06:00", heure_fin="07:00", poste_id=9999)
    # On simule une erreur de saisie : hack manuel de la durée
    t.duree = lambda: 25
    t.duree_formatee = lambda: "25h00min"

    mock_tranche_repo.list_all.return_value = [t]
    ok, alerts = service.validate_all()

    assert not ok
    assert any("impossible" in a.message.lower() for a in alerts)


# ------------------------------------------------------------------
# 7️⃣ Durée > 11h (warning)
# ------------------------------------------------------------------
def test_validate_all_long_amplitude(service, mock_tranche_repo):
    t = Tranche(id=1, nom="LONG", heure_debut="06:00", heure_fin="18:00", poste_id=9999)
    mock_tranche_repo.list_all.return_value = [t]

    ok, alerts = service.validate_all()
    assert ok  # warning, donc pas bloquant
    assert any("11h" in a.message.lower() for a in alerts)
    assert any(a.severity == Severity.WARNING for a in alerts)


# ------------------------------------------------------------------
# 9️⃣ validate_by_id - tranche introuvable
# ------------------------------------------------------------------
def test_validate_by_id_not_found(service, mock_tranche_repo):
    mock_tranche_repo.get.return_value = None
    ok, alerts = service.validate_by_id(99)
    assert not ok
    assert any("introuvable" in a.message.lower() for a in alerts)


# ------------------------------------------------------------------
# 🔟 validate_by_id - tranche valide
# ------------------------------------------------------------------
def test_validate_by_id_valid(service, mock_tranche_repo):
    t = Tranche(id=1, nom="MJ", heure_debut="07:00", heure_fin="15:00", poste_id=9999)
    mock_tranche_repo.get.return_value = t

    ok, alerts = service.validate_by_id(1)
    assert ok
    assert alerts == []
