from unittest.mock import create_autospec
import pytest

from core.application.services.regime_service import RegimeService
from core.application.ports import AgentRepositoryPort, RegimeRepositoryPort


@pytest.fixture
def repos():
    agent_repo = create_autospec(AgentRepositoryPort, instance=True)
    regime_repo = create_autospec(RegimeRepositoryPort, instance=True)
    return agent_repo, regime_repo


@pytest.fixture
def service(repos):
    agent_repo, regime_repo = repos
    return RegimeService(
        agent_repo=agent_repo,
        regime_repo=regime_repo,
    )


# =========================================================
# 🔹 get_regime_complet
# =========================================================
def test_get_regime_complet_retourne_none_si_absent(service, repos):
    agent_repo, regime_repo = repos
    regime_repo.get_by_id.return_value = None

    result = service.get_regime_complet(regime_id=123)

    assert result is None
    agent_repo.list_by_regime_id.assert_not_called()


def test_get_regime_complet_enrichit_agents(service, repos, make_regime, make_agent):
    agent_repo, regime_repo = repos

    r = make_regime(id=10, nom="R10")
    regime_repo.get_by_id.return_value = r

    agents = [make_agent(id=1, regime_id=10), make_agent(id=2, regime_id=10)]
    agent_repo.list_by_regime_id.return_value = agents

    result = service.get_regime_complet(regime_id=10)

    assert result is r
    regime_repo.get_by_id.assert_called_once_with(10)
    agent_repo.list_by_regime_id.assert_called_once_with(10)
    assert r.agents == agents


def test_get_regime_complet_met_agents_none_si_repo_renvoie_none(service, repos, make_regime):
    """
    Cas utile : si le repo renvoie None (au lieu de []), set_agents accepte Optional[List[Agent]].
    """
    agent_repo, regime_repo = repos

    r = make_regime(id=10, nom="R10")
    regime_repo.get_by_id.return_value = r

    agent_repo.list_by_regime_id.return_value = None

    result = service.get_regime_complet(regime_id=10)

    assert result is r
    assert r.agents is None


# =========================================================
# 🔹 list_regimes_complets
# =========================================================
def test_list_regimes_complets_enrichit_tous(service, repos, make_regime, make_agent):
    agent_repo, regime_repo = repos

    r1 = make_regime(id=1, nom="R1")
    r2 = make_regime(id=2, nom="R2")
    r3 = make_regime(id=3, nom="R3")
    regime_repo.list_all.return_value = [r1, r2, r3]

    agent_repo.list_by_regime_id.side_effect = lambda rid: [
        make_agent(id=rid * 100 + 1, regime_id=rid),
        make_agent(id=rid * 100 + 2, regime_id=rid),
    ]

    result = service.list_regimes_complets()

    assert result == [r1, r2, r3]
    regime_repo.list_all.assert_called_once_with()
    assert agent_repo.list_by_regime_id.call_count == 3

    assert r1.agents is not None and all(a.regime_id == 1 for a in r1.agents)
    assert r2.agents is not None and all(a.regime_id == 2 for a in r2.agents)
    assert r3.agents is not None and all(a.regime_id == 3 for a in r3.agents)


def test_list_regimes_complets_liste_vide(service, repos):
    agent_repo, regime_repo = repos
    regime_repo.list_all.return_value = []

    result = service.list_regimes_complets()

    assert result == []
    regime_repo.list_all.assert_called_once_with()
    agent_repo.list_by_regime_id.assert_not_called()
