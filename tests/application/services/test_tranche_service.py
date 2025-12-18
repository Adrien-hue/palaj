from unittest.mock import create_autospec
import pytest

from core.application.services.tranche_service import TrancheService
from core.application.ports import PosteRepositoryPort, TrancheRepositoryPort


@pytest.fixture
def repos():
    poste_repo = create_autospec(PosteRepositoryPort, instance=True)
    tranche_repo = create_autospec(TrancheRepositoryPort, instance=True)
    return poste_repo, tranche_repo


@pytest.fixture
def service(repos):
    poste_repo, tranche_repo = repos
    return TrancheService(
        poste_repo=poste_repo,
        tranche_repo=tranche_repo,
    )


# =========================================================
# 🔹 Chargement (delegation)
# =========================================================
def test_list_all_delegue_au_repo(service, repos, make_tranche):
    _, tranche_repo = repos
    tranches = [make_tranche(id=1), make_tranche(id=2)]
    tranche_repo.list_all.return_value = tranches

    result = service.list_all()

    assert result == tranches
    tranche_repo.list_all.assert_called_once_with()


def test_get_by_id_delegue_au_repo(service, repos, make_tranche):
    _, tranche_repo = repos
    t = make_tranche(id=42)
    tranche_repo.get_by_id.return_value = t

    result = service.get_by_id(42)

    assert result is t
    tranche_repo.get_by_id.assert_called_once_with(42)


def test_list_by_poste_id_delegue_au_repo(service, repos, make_tranche):
    _, tranche_repo = repos
    tranches = [make_tranche(id=1, poste_id=10), make_tranche(id=2, poste_id=10)]
    tranche_repo.list_by_poste_id.return_value = tranches

    result = service.list_by_poste_id(10)

    assert result == tranches
    tranche_repo.list_by_poste_id.assert_called_once_with(10)


# =========================================================
# 🔹 Chargement complet
# =========================================================
def test_get_tranche_complet_retourne_none_si_absente(service, repos):
    poste_repo, tranche_repo = repos
    tranche_repo.get_by_id.return_value = None

    result = service.get_tranche_complet(tranche_id=123)

    assert result is None
    poste_repo.get_by_id.assert_not_called()


def test_get_tranche_complet_enrichit_poste(service, repos, make_tranche, make_poste):
    poste_repo, tranche_repo = repos

    t = make_tranche(id=7, poste_id=99)
    tranche_repo.get_by_id.return_value = t

    p = make_poste(id=99, nom="GM J")
    poste_repo.get_by_id.return_value = p

    result = service.get_tranche_complet(tranche_id=7)

    assert result is t
    tranche_repo.get_by_id.assert_called_once_with(7)
    poste_repo.get_by_id.assert_called_once_with(99)
    assert t.poste is p


def test_get_tranche_complet_met_poste_a_none_si_introuvable(service, repos, make_tranche):
    poste_repo, tranche_repo = repos

    t = make_tranche(id=7, poste_id=999)
    tranche_repo.get_by_id.return_value = t

    poste_repo.get_by_id.return_value = None

    result = service.get_tranche_complet(tranche_id=7)

    assert result is t
    assert t.poste is None


def test_list_tranches_complets_enrichit_toutes(service, repos, make_tranche, make_poste):
    poste_repo, tranche_repo = repos

    t1 = make_tranche(id=1, poste_id=10)
    t2 = make_tranche(id=2, poste_id=20)
    t3 = make_tranche(id=3, poste_id=30)
    tranche_repo.list_all.return_value = [t1, t2, t3]

    poste_repo.get_by_id.side_effect = lambda pid: make_poste(id=pid, nom=f"P{pid}")

    result = service.list_tranches_complets()

    assert result == [t1, t2, t3]
    tranche_repo.list_all.assert_called_once_with()
    assert poste_repo.get_by_id.call_count == 3

    assert t1.poste is not None and t1.poste.id == 10
    assert t2.poste is not None and t2.poste.id == 20
    assert t3.poste is not None and t3.poste.id == 30


def test_list_tranches_complets_liste_vide(service, repos):
    poste_repo, tranche_repo = repos
    tranche_repo.list_all.return_value = []

    result = service.list_tranches_complets()

    assert result == []
    tranche_repo.list_all.assert_called_once_with()
    poste_repo.get_by_id.assert_not_called()
