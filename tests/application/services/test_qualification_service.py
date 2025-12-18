from unittest.mock import create_autospec
import pytest

from core.application.services.qualification_service import QualificationService
from core.application.ports import (
    AgentRepositoryPort,
    PosteRepositoryPort,
    QualificationRepositoryPort,
)


@pytest.fixture
def repos():
    agent_repo = create_autospec(AgentRepositoryPort, instance=True)
    poste_repo = create_autospec(PosteRepositoryPort, instance=True)
    qualification_repo = create_autospec(QualificationRepositoryPort, instance=True)
    return agent_repo, poste_repo, qualification_repo


@pytest.fixture
def service(repos):
    agent_repo, poste_repo, qualification_repo = repos
    return QualificationService(
        agent_repo=agent_repo,
        poste_repo=poste_repo,
        qualification_repo=qualification_repo,
    )


# =========================================================
# 🔹 Chargement (delegation)
# =========================================================
def test_list_qualifications_delegue_au_repo(service, repos, make_qualification):
    _, _, qualification_repo = repos
    quals = [make_qualification(agent_id=1, poste_id=10), make_qualification(agent_id=2, poste_id=20)]
    qualification_repo.list_all.return_value = quals

    result = service.list_qualifications()

    assert result == quals
    qualification_repo.list_all.assert_called_once_with()


def test_list_for_agent_delegue_au_repo(service, repos, make_qualification):
    _, _, qualification_repo = repos
    quals = [make_qualification(agent_id=7, poste_id=1)]
    qualification_repo.list_for_agent.return_value = quals

    result = service.list_for_agent(agent_id=7)

    assert result == quals
    qualification_repo.list_for_agent.assert_called_once_with(7)


def test_list_for_poste_delegue_au_repo(service, repos, make_qualification):
    _, _, qualification_repo = repos
    quals = [make_qualification(agent_id=7, poste_id=99)]
    qualification_repo.list_for_poste.return_value = quals

    result = service.list_for_poste(poste_id=99)

    assert result == quals
    qualification_repo.list_for_poste.assert_called_once_with(99)


# =========================================================
# 🔹 Chargement complet
# =========================================================
def test_get_qualification_complet_retourne_none_si_absente(service, repos):
    agent_repo, poste_repo, qualification_repo = repos
    qualification_repo.get_for_agent_and_poste.return_value = None

    result = service.get_qualification_complet(agent_id=1, poste_id=2)

    assert result is None
    agent_repo.get_by_id.assert_not_called()
    poste_repo.get_by_id.assert_not_called()


def test_get_qualification_complet_enrichit_agent_et_poste(
    service,
    repos,
    make_qualification,
    make_agent,
    make_poste,
):
    agent_repo, poste_repo, qualification_repo = repos

    q = make_qualification(agent_id=42, poste_id=7)
    qualification_repo.get_for_agent_and_poste.return_value = q

    agent = make_agent(id=42)
    poste = make_poste(id=7)

    agent_repo.get_by_id.return_value = agent
    poste_repo.get_by_id.return_value = poste

    result = service.get_qualification_complet(agent_id=42, poste_id=7)

    assert result is q

    qualification_repo.get_for_agent_and_poste.assert_called_once_with(42, 7)
    agent_repo.get_by_id.assert_called_once_with(42)
    poste_repo.get_by_id.assert_called_once_with(7)

    assert q.agent is agent
    assert q.poste is poste


def test_get_qualification_complet_met_none_si_agent_ou_poste_introuvable(
    service,
    repos,
    make_qualification,
):
    agent_repo, poste_repo, qualification_repo = repos

    q = make_qualification(agent_id=999, poste_id=888)
    qualification_repo.get_for_agent_and_poste.return_value = q

    agent_repo.get_by_id.return_value = None
    poste_repo.get_by_id.return_value = None

    result = service.get_qualification_complet(agent_id=999, poste_id=888)

    assert result is q
    assert q.agent is None
    assert q.poste is None


def test_list_qualifications_complets_enrichit_toutes(
    service,
    repos,
    make_qualification,
    make_agent,
    make_poste,
):
    agent_repo, poste_repo, qualification_repo = repos

    q1 = make_qualification(agent_id=1, poste_id=10)
    q2 = make_qualification(agent_id=2, poste_id=20)
    qualification_repo.list_all.return_value = [q1, q2]

    agent_repo.get_by_id.side_effect = lambda aid: make_agent(id=aid)
    poste_repo.get_by_id.side_effect = lambda pid: make_poste(id=pid)

    result = service.list_qualifications_complets()

    assert result == [q1, q2]
    qualification_repo.list_all.assert_called_once_with()

    assert agent_repo.get_by_id.call_count == 2
    assert poste_repo.get_by_id.call_count == 2

    assert q1.agent is not None and q1.agent.id == 1
    assert q1.poste is not None and q1.poste.id == 10
    assert q2.agent is not None and q2.agent.id == 2
    assert q2.poste is not None and q2.poste.id == 20


def test_list_qualifications_complets_liste_vide(service, repos):
    agent_repo, poste_repo, qualification_repo = repos
    qualification_repo.list_all.return_value = []

    result = service.list_qualifications_complets()

    assert result == []
    qualification_repo.list_all.assert_called_once_with()
    agent_repo.get_by_id.assert_not_called()
    poste_repo.get_by_id.assert_not_called()


# =========================================================
# 🔹 Vérifications
# =========================================================
def test_is_qualified_delegue_au_repo(service, repos):
    _, _, qualification_repo = repos
    qualification_repo.is_qualified.return_value = True

    result = service.is_qualified(agent_id=1, poste_id=2)

    assert result is True
    qualification_repo.is_qualified.assert_called_once_with(1, 2)
