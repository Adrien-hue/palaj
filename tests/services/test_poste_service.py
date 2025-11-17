import pytest
from core.domain.services.poste_validator_service import PosteValidatorService
from core.domain.entities import Poste, Tranche
from core.utils.domain_alert import Severity


@pytest.fixture
def mock_poste_repo(mocker):
    return mocker.Mock()


@pytest.fixture
def mock_tranche_repo(mocker):
    return mocker.Mock()


@pytest.fixture
def service(mock_poste_repo, mock_tranche_repo):
    return PosteValidatorService()


# ------------------------------------------------------------------
# 1️⃣ Aucun poste
# ------------------------------------------------------------------

def test_validate_all_empty(service, mock_poste_repo):
    mock_poste_repo.list_all.return_value = []
    ok, alerts = service.validate_all()

    assert ok is True
    assert alerts == []


# ------------------------------------------------------------------
# 2️⃣ Un seul poste valide avec tranches existantes
# ------------------------------------------------------------------

def test_validate_all_valid_poste(service, mock_poste_repo, mock_tranche_repo):
    tranche = Tranche(id=1, nom="M1", heure_debut="08:00", heure_fin="16:00", poste_id=9999)
    poste = Poste(id=9999, nom="RLIV")

    mock_poste_repo.list_all.return_value = [poste]
    mock_tranche_repo.get.return_value = tranche  # ✅ tranche existante

    ok, alerts = service.validate_all()

    assert ok is True
    assert alerts == []
    mock_tranche_repo.get.assert_called_once_with(1)


# ------------------------------------------------------------------
# 3️⃣ Poste avec tranche manquante
# ------------------------------------------------------------------

def test_validate_all_missing_tranche(service, mock_poste_repo, mock_tranche_repo):
    poste = Poste(id=9999, nom="GM")
    mock_poste_repo.list_all.return_value = [poste]
    mock_tranche_repo.get.return_value = None  # ❌ tranche inexistante

    ok, alerts = service.validate_all()

    assert ok is False
    assert len(alerts) == 1
    assert "tranche inexistante" in alerts[0].message.lower()
    assert alerts[0].severity == Severity.ERROR
    assert alerts[0].source == "PosteValidatorService"


# ------------------------------------------------------------------
# 4️⃣ Deux postes avec ID doublonné
# ------------------------------------------------------------------

def test_validate_all_duplicate_poste(service, mock_poste_repo, mock_tranche_repo):
    p1 = Poste(id=9999, nom="RLIV1")
    p2 = Poste(id=9999, nom="RLIV2")  # ❌ même ID

    mock_poste_repo.list_all.return_value = [p1, p2]
    mock_tranche_repo.get.return_value = Tranche(id=1, nom="M1", heure_debut="08:00", heure_fin="16:00", poste_id=9999)

    ok, alerts = service.validate_all()

    assert not ok
    assert any("doublon" in a.message.lower() for a in alerts)
    assert all(a.source == "PosteValidatorService" for a in alerts)


# ------------------------------------------------------------------
# 5️⃣ Poste avec plusieurs tranches dont une manquante
# ------------------------------------------------------------------

def test_validate_all_mixed_tranches(service, mock_poste_repo, mock_tranche_repo):
    t1 = Tranche(id=1, nom="J1", heure_debut="06:00", heure_fin="14:00", poste_id=9999)
    t2 = Tranche(id=2, nom="J2", heure_debut="14:00", heure_fin="22:00", poste_id=9999)
    poste = Poste(id=9999, nom="RLIV")

    mock_poste_repo.list_all.return_value = [poste]
    mock_tranche_repo.get.side_effect = lambda tid: t1 if tid == 1 else (t2 if tid == 2 else None)

    ok, alerts = service.validate_all()

    assert not ok
    assert any("tranche inexistante" in a.message.lower() for a in alerts)
    assert len(alerts) == 1
    assert alerts[0].severity == Severity.ERROR


# ------------------------------------------------------------------
# 6️⃣ Plusieurs postes valides
# ------------------------------------------------------------------

def test_validate_all_multiple_valid(service, mock_poste_repo, mock_tranche_repo):
    t1 = Tranche(id=1, nom="M1", heure_debut="08:00", heure_fin="16:00", poste_id=9999)
    t2 = Tranche(id=2, nom="M2", heure_debut="09:00", heure_fin="17:00", poste_id=9999)

    p1 = Poste(id=9999, nom="RLIV1")
    p2 = Poste(id=9999, nom="RLIV2")

    mock_poste_repo.list_all.return_value = [p1, p2]
    mock_tranche_repo.get.side_effect = lambda tid: t1 if tid == 1 else t2

    ok, alerts = service.validate_all()

    assert ok is True
    assert alerts == []
