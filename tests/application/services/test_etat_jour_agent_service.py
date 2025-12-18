from datetime import date
from unittest.mock import create_autospec

import pytest

from core.application.services.etat_jour_agent_service import EtatJourAgentService
from core.application.ports import (
    AffectationRepositoryPort,
    AgentRepositoryPort,
    EtatJourAgentRepositoryPort,
)


@pytest.fixture
def repos():
    affectation_repo = create_autospec(AffectationRepositoryPort, instance=True)
    agent_repo = create_autospec(AgentRepositoryPort, instance=True)
    etat_repo = create_autospec(EtatJourAgentRepositoryPort, instance=True)
    return affectation_repo, agent_repo, etat_repo


@pytest.fixture
def service(repos):
    affectation_repo, agent_repo, etat_repo = repos
    return EtatJourAgentService(
        affectation_repo=affectation_repo,
        agent_repo=agent_repo,
        etat_jour_agent_repo=etat_repo,
    )


# =========================================================
# 🔹 Chargement (delegation)
# =========================================================
def test_list_all_delegue_au_repo(service, repos, make_etat_jour_agent):
    _, _, etat_repo = repos
    fake_list = [make_etat_jour_agent(agent_id=1), make_etat_jour_agent(agent_id=2)]
    etat_repo.list_all.return_value = fake_list

    result = service.list_all()

    assert result == fake_list
    etat_repo.list_all.assert_called_once_with()


def test_list_between_dates_delegue_au_repo(service, repos, make_etat_jour_agent):
    _, _, etat_repo = repos
    d1 = date(2025, 1, 1)
    d2 = date(2025, 1, 31)
    fake_list = [make_etat_jour_agent(agent_id=1, jour=d1)]
    etat_repo.list_between_dates.return_value = fake_list

    result = service.list_between_dates(d1, d2)

    assert result == fake_list
    etat_repo.list_between_dates.assert_called_once_with(d1, d2)


def test_list_for_agent_delegue_au_repo(service, repos, make_etat_jour_agent):
    _, _, etat_repo = repos
    fake_list = [make_etat_jour_agent(agent_id=7)]
    etat_repo.list_for_agent.return_value = fake_list

    result = service.list_for_agent(agent_id=7)

    assert result == fake_list
    etat_repo.list_for_agent.assert_called_once_with(7)


def test_list_for_agent_between_dates_delegue_au_repo(service, repos, make_etat_jour_agent):
    _, _, etat_repo = repos
    d1 = date(2025, 1, 1)
    d2 = date(2025, 1, 7)
    fake_list = [make_etat_jour_agent(agent_id=7, jour=d1)]
    etat_repo.list_for_agent_between_dates.return_value = fake_list

    result = service.list_for_agent_between_dates(agent_id=7, date_start=d1, date_end=d2)

    assert result == fake_list
    etat_repo.list_for_agent_between_dates.assert_called_once_with(7, d1, d2)


def test_get_for_agent_and_day_delegue_au_repo(service, repos, make_etat_jour_agent):
    _, _, etat_repo = repos
    j = date(2025, 1, 2)
    etat = make_etat_jour_agent(agent_id=42, jour=j)
    etat_repo.get_for_agent_and_day.return_value = etat

    result = service.get_for_agent_and_day(agent_id=42, jour=j)

    assert result == etat
    etat_repo.get_for_agent_and_day.assert_called_once_with(42, j)


# =========================================================
# 🔹 Chargement complet
# =========================================================
def test_get_etat_jour_agent_complet_retourne_none_si_absent(service, repos):
    _, agent_repo, etat_repo = repos
    etat_repo.get_for_agent_and_day.return_value = None

    result = service.get_etat_jour_agent_complet(agent_id=1, jour=date(2025, 1, 1))

    assert result is None
    agent_repo.get_by_id.assert_not_called()


def test_get_etat_jour_agent_complet_enrichit_agent(service, repos, make_etat_jour_agent, make_agent):
    _, agent_repo, etat_repo = repos
    j = date(2025, 1, 1)

    etat = make_etat_jour_agent(agent_id=42, jour=j)
    etat_repo.get_for_agent_and_day.return_value = etat

    agent = make_agent(id=42)
    agent_repo.get_by_id.return_value = agent

    result = service.get_etat_jour_agent_complet(agent_id=42, jour=j)

    assert result is etat
    etat_repo.get_for_agent_and_day.assert_called_once_with(42, j)
    agent_repo.get_by_id.assert_called_once_with(42)
    assert etat.agent is agent


def test_get_etat_jour_agent_complet_met_agent_a_none_si_introuvable(service, repos, make_etat_jour_agent):
    """
    Cas utile: l'état existe mais l'agent n'existe pas (ou repo renvoie None).
    On valide que ça ne crash pas et que l'enrichissement pose bien None.
    """
    _, agent_repo, etat_repo = repos
    j = date(2025, 1, 1)

    etat = make_etat_jour_agent(agent_id=999, jour=j)
    etat_repo.get_for_agent_and_day.return_value = etat

    agent_repo.get_by_id.return_value = None

    result = service.get_etat_jour_agent_complet(agent_id=999, jour=j)

    assert result is etat
    agent_repo.get_by_id.assert_called_once_with(999)
    assert etat.agent is None


def test_list_etats_jour_agent_complets_enrichit_tous(service, repos, make_etat_jour_agent, make_agent):
    _, agent_repo, etat_repo = repos

    e1 = make_etat_jour_agent(agent_id=1)
    e2 = make_etat_jour_agent(agent_id=2)
    e3 = make_etat_jour_agent(agent_id=3)
    etat_repo.list_all.return_value = [e1, e2, e3]

    agent_repo.get_by_id.side_effect = lambda aid: make_agent(id=aid)

    result = service.list_etats_jour_agent_complets()

    assert result == [e1, e2, e3]
    etat_repo.list_all.assert_called_once_with()
    assert agent_repo.get_by_id.call_count == 3

    assert e1.agent is not None and e1.agent.id == 1
    assert e2.agent is not None and e2.agent.id == 2
    assert e3.agent is not None and e3.agent.id == 3


def test_list_etats_jour_agent_complets_liste_vide(service, repos):
    _, agent_repo, etat_repo = repos
    etat_repo.list_all.return_value = []

    result = service.list_etats_jour_agent_complets()

    assert result == []
    etat_repo.list_all.assert_called_once_with()
    agent_repo.get_by_id.assert_not_called()
