from unittest.mock import create_autospec
import pytest

from core.application.services.poste_service import PosteService
from core.application.ports import (
    PosteRepositoryPort,
    QualificationRepositoryPort,
    TrancheRepositoryPort,
)

@pytest.fixture
def repos():
    poste_repo = create_autospec(PosteRepositoryPort, instance=True)
    qualification_repo = create_autospec(QualificationRepositoryPort, instance=True)
    tranche_repo = create_autospec(TrancheRepositoryPort, instance=True)
    return poste_repo, qualification_repo, tranche_repo

@pytest.fixture
def service(repos):
    poste_repo, qualification_repo, tranche_repo = repos
    return PosteService(
        poste_repo=poste_repo,
        qualification_repo=qualification_repo,
        tranche_repo=tranche_repo,
    )

# =========================================================
# 🔹 Delegation simple
# =========================================================
def test_get_by_id_delegue_au_repo(service, repos, make_poste):
    poste_repo, _, _ = repos
    p = make_poste(id=1, nom="GM J")
    poste_repo.get_by_id.return_value = p

    result = service.get_by_id(1)

    assert result is p
    poste_repo.get_by_id.assert_called_once_with(1)


def test_list_all_delegue_au_repo(service, repos, make_poste):
    poste_repo, _, _ = repos
    postes = [make_poste(id=1, nom="A"), make_poste(id=2, nom="B")]
    poste_repo.list_all.return_value = postes

    result = service.list_all()

    assert result == postes
    poste_repo.list_all.assert_called_once_with()


# =========================================================
# 🔹 Chargement complet
# =========================================================
def test_get_poste_complet_retourne_none_si_absent(service, repos):
    poste_repo, qualification_repo, tranche_repo = repos
    poste_repo.get_by_id.return_value = None

    result = service.get_poste_complet(poste_id=123)

    assert result is None
    tranche_repo.list_by_poste_id.assert_not_called()
    qualification_repo.list_for_poste.assert_not_called()


def test_get_poste_complet_enrichit_tranches_et_qualifs(
    service,
    repos,
    make_poste,
    make_tranche,
    make_qualification,
):
    poste_repo, qualification_repo, tranche_repo = repos
    p = make_poste(id=10, nom="RLIV")
    poste_repo.get_by_id.return_value = p

    tranches = [
        make_tranche(id=1, poste_id=10, nom="M"),
        make_tranche(id=2, poste_id=10, nom="S"),
    ]
    qualifications = [
        make_qualification(agent_id=1, poste_id=10),
        make_qualification(agent_id=2, poste_id=10),
    ]

    tranche_repo.list_by_poste_id.return_value = tranches
    qualification_repo.list_for_poste.return_value = qualifications

    result = service.get_poste_complet(poste_id=10)

    assert result is p
    poste_repo.get_by_id.assert_called_once_with(10)
    tranche_repo.list_by_poste_id.assert_called_once_with(10)
    qualification_repo.list_for_poste.assert_called_once_with(10)

    assert p.tranches == tranches
    assert p.qualifications == qualifications


def test_list_postes_complets_enrichit_tous_les_postes(
    service,
    repos,
    make_poste,
    make_tranche,
    make_qualification,
):
    poste_repo, qualification_repo, tranche_repo = repos

    p1 = make_poste(id=1, nom="P1")
    p2 = make_poste(id=2, nom="P2")
    p3 = make_poste(id=3, nom="P3")
    poste_repo.list_all.return_value = [p1, p2, p3]

    tranche_repo.list_by_poste_id.side_effect = lambda poste_id: [
        make_tranche(id=poste_id * 10 + 1, poste_id=poste_id, nom=f"T{poste_id}")
    ]
    qualification_repo.list_for_poste.side_effect = lambda poste_id: [
        make_qualification(agent_id=999, poste_id=poste_id)
    ]

    result = service.list_postes_complets()

    assert result == [p1, p2, p3]
    poste_repo.list_all.assert_called_once_with()

    assert tranche_repo.list_by_poste_id.call_count == 3
    assert qualification_repo.list_for_poste.call_count == 3

    assert len(p1.tranches) == 1 and p1.tranches[0].poste_id == 1
    assert len(p2.tranches) == 1 and p2.tranches[0].poste_id == 2
    assert len(p3.tranches) == 1 and p3.tranches[0].poste_id == 3

    assert len(p1.qualifications) == 1 and p1.qualifications[0].poste_id == 1
    assert len(p2.qualifications) == 1 and p2.qualifications[0].poste_id == 2
    assert len(p3.qualifications) == 1 and p3.qualifications[0].poste_id == 3


def test_list_postes_complets_liste_vide(service, repos):
    poste_repo, qualification_repo, tranche_repo = repos
    poste_repo.list_all.return_value = []

    result = service.list_postes_complets()

    assert result == []
    poste_repo.list_all.assert_called_once_with()
    tranche_repo.list_by_poste_id.assert_not_called()
    qualification_repo.list_for_poste.assert_not_called()