from datetime import date
from unittest.mock import create_autospec

import pytest

from core.application.services.affectation_service import AffectationService
from core.application.ports import (
    AffectationRepositoryPort,
    AgentRepositoryPort,
    TrancheRepositoryPort,
)


@pytest.fixture
def repos():
    # autospec => méthodes autorisées = celles du Protocol
    affectation_repo = create_autospec(AffectationRepositoryPort, instance=True)
    agent_repo = create_autospec(AgentRepositoryPort, instance=True)
    tranche_repo = create_autospec(TrancheRepositoryPort, instance=True)
    return affectation_repo, agent_repo, tranche_repo


@pytest.fixture
def service(repos):
    affectation_repo, agent_repo, tranche_repo = repos
    return AffectationService(
        affectation_repo=affectation_repo,
        agent_repo=agent_repo,
        tranche_repo=tranche_repo,
    )

def test_list_affectations_delegue_au_repo(service, repos, make_affectation):
    affectation_repo, _, _ = repos
    fake_list = [make_affectation(agent_id=1, tranche_id=10), make_affectation(agent_id=2, tranche_id=20)]
    affectation_repo.list_all.return_value = fake_list

    result = service.list_affectations()

    assert result == fake_list
    affectation_repo.list_all.assert_called_once_with()


def test_list_for_agent_delegue_au_repo(service, repos, make_affectation):
    affectation_repo, _, _ = repos
    fake_list = [make_affectation(agent_id=7, tranche_id=99)]
    affectation_repo.list_for_agent.return_value = fake_list

    result = service.list_for_agent(agent_id=7)

    assert result == fake_list
    affectation_repo.list_for_agent.assert_called_once_with(7)


def test_list_for_day_delegue_au_repo(service, repos, make_affectation):
    affectation_repo, _, _ = repos
    j = date(2025, 1, 2)
    fake_list = [make_affectation(agent_id=1, tranche_id=10, jour=j)]
    affectation_repo.list_for_day.return_value = fake_list

    result = service.list_for_day(j)

    assert result == fake_list
    affectation_repo.list_for_day.assert_called_once_with(j)


def test_list_for_poste_delegue_au_repo(service, repos, make_affectation):
    affectation_repo, _, _ = repos
    start = date(2025, 1, 1)
    end = date(2025, 1, 31)
    fake_list = [make_affectation(agent_id=1, tranche_id=10)]
    affectation_repo.list_for_poste.return_value = fake_list

    result = service.list_for_poste(poste_id=3, start=start, end=end)

    assert result == fake_list
    affectation_repo.list_for_poste.assert_called_once_with(3, start, end)


def test_get_affectation_complet_retourne_none_si_absente(service, repos):
    affectation_repo, agent_repo, tranche_repo = repos
    affectation_repo.get_for_agent_and_day.return_value = None

    result = service.get_affectation_complet(agent_id=1, jour=date(2025, 1, 1))

    assert result is None
    agent_repo.get_by_id.assert_not_called()
    tranche_repo.get_by_id.assert_not_called()


def test_get_affectation_complet_enrichit_agent_et_tranche(service, repos, make_affectation):
    affectation_repo, agent_repo, tranche_repo = repos
    j = date(2025, 1, 1)

    a = make_affectation(agent_id=42, tranche_id=8, jour=j)
    affectation_repo.get_for_agent_and_day.return_value = a

    fake_agent = object()
    fake_tranche = object()
    agent_repo.get_by_id.return_value = fake_agent
    tranche_repo.get_by_id.return_value = fake_tranche

    result = service.get_affectation_complet(agent_id=42, jour=j)

    assert result is a
    assert a.agent is fake_agent
    assert a.tranche is fake_tranche

    affectation_repo.get_for_agent_and_day.assert_called_once_with(42, j)
    agent_repo.get_by_id.assert_called_once_with(42)
    tranche_repo.get_by_id.assert_called_once_with(8)


def test_list_affectations_completes_enrichit_toutes_les_affectations(service, repos, make_affectation):
    affectation_repo, agent_repo, tranche_repo = repos

    a1 = make_affectation(agent_id=1, tranche_id=10)
    a2 = make_affectation(agent_id=2, tranche_id=20)
    affectation_repo.list_all.return_value = [a1, a2]

    agent_repo.get_by_id.side_effect = lambda agent_id: f"agent:{agent_id}"
    tranche_repo.get_by_id.side_effect = lambda tranche_id: f"tranche:{tranche_id}"

    result = service.list_affectations_completes()

    assert result == [a1, a2]
    assert a1.agent == "agent:1"
    assert a1.tranche == "tranche:10"
    assert a2.agent == "agent:2"
    assert a2.tranche == "tranche:20"

    affectation_repo.list_all.assert_called_once_with()
    assert agent_repo.get_by_id.call_count == 2
    assert tranche_repo.get_by_id.call_count == 2
