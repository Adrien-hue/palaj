import pytest
from datetime import time
from core.domain.services.tranche_service import TrancheService
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
    t = Tranche(id=1, abbr="MJ", debut="08:00", fin="16:00", nb_agents_requis=2)
    mock_tranche_repo.list_all.return_value = [t]

    ok, alerts = service.validate_all()
    assert ok
    assert alerts == []


# ------------------------------------------------------------------
# 3️⃣ Doublon d’ID
# ------------------------------------------------------------------
def test_validate_all_duplicate(service, mock_tranche_repo):
    t1 = Tranche(id=1, abbr="MJ1", debut="07:00", fin="15:00")
    t2 = Tranche(id=1, abbr="MJ2", debut="09:00", fin="17:00")
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
    t1 = Tranche(id=1, abbr="INCOMPLETE", debut=None, fin="12:00")
    t2 = Tranche(id=2, abbr="INCOMPLETE2", debut="08:00", fin=None)
    mock_tranche_repo.list_all.return_value = [t1, t2]

    ok, alerts = service.validate_all()
    assert not ok
    assert len(alerts) == 2
    assert all("horaires incomplets" in a.message.lower() for a in alerts)


# ------------------------------------------------------------------
# 5️⃣ Durée nulle
# ------------------------------------------------------------------
def test_validate_all_zero_duration(service, mock_tranche_repo):
    t = Tranche(id=1, abbr="ZERO", debut="08:00", fin="08:00")
    mock_tranche_repo.list_all.return_value = [t]

    ok, alerts = service.validate_all()
    assert not ok
    assert any("durée nulle" in a.message.lower() for a in alerts)


# ------------------------------------------------------------------
# 6️⃣ Durée > 24h (impossible)
# ------------------------------------------------------------------
def test_validate_all_duration_over_24h(service, mock_tranche_repo):
    t = Tranche(id=1, abbr="LONGUE", debut="06:00", fin="07:00")
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
    t = Tranche(id=1, abbr="LONG", debut="06:00", fin="18:00")
    mock_tranche_repo.list_all.return_value = [t]

    ok, alerts = service.validate_all()
    assert ok  # warning, donc pas bloquant
    assert any("11h" in a.message.lower() for a in alerts)
    assert any(a.severity == Severity.WARNING for a in alerts)


# ------------------------------------------------------------------
# 8️⃣ Nombre d’agents requis invalide
# ------------------------------------------------------------------
def test_validate_all_invalid_nb_agents(service, mock_tranche_repo):
    t = Tranche(id=1, abbr="NEG", debut="08:00", fin="12:00", nb_agents_requis=0)
    mock_tranche_repo.list_all.return_value = [t]

    ok, alerts = service.validate_all()
    assert not ok
    assert any("nb_agents_requis" in a.message.lower() for a in alerts)
    assert any(a.severity == Severity.ERROR for a in alerts)


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
    t = Tranche(id=1, abbr="MJ", debut="07:00", fin="15:00")
    mock_tranche_repo.get.return_value = t

    ok, alerts = service.validate_by_id(1)
    assert ok
    assert alerts == []
