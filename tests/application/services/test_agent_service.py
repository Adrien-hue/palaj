from unittest.mock import create_autospec
import pytest

from core.application.services.agent_service import AgentService
from core.application.ports import (
    AffectationRepositoryPort,
    AgentRepositoryPort,
    EtatJourAgentRepositoryPort,
    QualificationRepositoryPort,
    RegimeRepositoryPort,
)


@pytest.fixture
def repos():
    affectation_repo = create_autospec(AffectationRepositoryPort, instance=True)
    agent_repo = create_autospec(AgentRepositoryPort, instance=True)
    etat_repo = create_autospec(EtatJourAgentRepositoryPort, instance=True)
    qualification_repo = create_autospec(QualificationRepositoryPort, instance=True)
    regime_repo = create_autospec(RegimeRepositoryPort, instance=True)
    return affectation_repo, agent_repo, etat_repo, qualification_repo, regime_repo


@pytest.fixture
def service(repos):
    affectation_repo, agent_repo, qualification_repo, regime_repo = repos
    return AgentService(
        affectation_repo=affectation_repo,
        agent_repo=agent_repo,
        qualification_repo=qualification_repo,
        regime_repo=regime_repo,
    )


# =========================================================
# 🔹 Delegation simple
# =========================================================
def test_list_all_delegue_au_repo(service, repos, make_agent):
    _, agent_repo, *_ = repos
    agents = [make_agent(id=1), make_agent(id=2)]
    agent_repo.list_all.return_value = agents

    result = service.list_all()

    assert result == agents
    agent_repo.list_all.assert_called_once_with()


def test_get_by_id_delegue_au_repo(service, repos, make_agent):
    _, agent_repo, *_ = repos
    agent = make_agent(id=42)
    agent_repo.get_by_id.return_value = agent

    result = service.get_by_id(42)

    assert result is agent
    agent_repo.get_by_id.assert_called_once_with(42)


# =========================================================
# 🔹 get_agent_complet
# =========================================================
def test_get_agent_complet_retourne_none_si_absent(service, repos):
    affectation_repo, agent_repo, etat_repo, qualification_repo, regime_repo = repos
    agent_repo.get_by_id.return_value = None

    result = service.get_agent_complet(agent_id=999)

    assert result is None
    regime_repo.get_by_id.assert_not_called()
    affectation_repo.list_for_agent.assert_not_called()
    etat_repo.list_for_agent.assert_not_called()
    qualification_repo.list_for_agent.assert_not_called()


def test_get_agent_complet_charge_tout_avec_regime(service, repos, make_agent, make_affectation, make_regime, make_qualification):
    affectation_repo, agent_repo, etat_repo, qualification_repo, regime_repo = repos

    agent = make_agent(id=42, regime_id=7)
    agent_repo.get_by_id.return_value = agent

    regime = make_regime(id=7, nom="R1")
    affectations = [make_affectation(agent_id=42, tranche_id=10)]
    qualifications = [make_qualification(agent_id=42)]

    regime_repo.get_by_id.return_value = regime
    affectation_repo.list_for_agent.return_value = affectations
    qualification_repo.list_for_agent.return_value = qualifications

    result = service.get_agent_complet(agent_id=42)

    assert result is agent

    # Appels repos
    agent_repo.get_by_id.assert_called_once_with(42)
    regime_repo.get_by_id.assert_called_once_with(7)
    affectation_repo.list_for_agent.assert_called_once_with(42)
    etat_repo.list_for_agent.assert_called_once_with(42)
    qualification_repo.list_for_agent.assert_called_once_with(42)

    # Enrichissements agent (avec TES propriétés)
    assert agent.regime is regime
    assert agent.affectations == affectations
    assert agent.etat_jours == etats
    assert agent.qualifications == qualifications


def test_get_agent_complet_ne_charge_pas_regime_si_regime_id_none(service, repos, make_agent):
    affectation_repo, agent_repo, etat_repo, qualification_repo, regime_repo = repos

    agent = make_agent(id=42, regime_id=None)
    agent_repo.get_by_id.return_value = agent

    affectation_repo.list_for_agent.return_value = []
    etat_repo.list_for_agent.return_value = []
    qualification_repo.list_for_agent.return_value = []

    result = service.get_agent_complet(agent_id=42)

    assert result is agent

    regime_repo.get_by_id.assert_not_called()
    affectation_repo.list_for_agent.assert_called_once_with(42)
    etat_repo.list_for_agent.assert_called_once_with(42)
    qualification_repo.list_for_agent.assert_called_once_with(42)

    # régime pas set => reste None
    assert agent.regime is None


# =========================================================
# 🔹 list_agents_complets
# =========================================================
def test_list_agents_complets_enrichit_tous_les_agents(service, repos, make_agent, make_regime):
    affectation_repo, agent_repo, etat_repo, qualification_repo, regime_repo = repos

    a1 = make_agent(id=1, regime_id=10)
    a2 = make_agent(id=2, regime_id=None)
    a3 = make_agent(id=3, regime_id=30)
    agent_repo.list_all.return_value = [a1, a2, a3]

    regime_repo.get_by_id.side_effect = lambda rid: make_regime(id=rid, nom=f"R{rid}")
    affectation_repo.list_for_agent.side_effect = lambda aid: [f"aff:{aid}"]
    etat_repo.list_for_agent.side_effect = lambda aid: [f"etat:{aid}"]
    qualification_repo.list_for_agent.side_effect = lambda aid: [f"qualif:{aid}"]

    result = service.list_agents_complets()

    assert result == [a1, a2, a3]

    # regime uniquement si regime_id
    assert a1.regime is not None and a1.regime.nom == "R10"
    assert a2.regime is None
    assert a3.regime is not None and a3.regime.nom == "R30"

    # enrichissements
    assert a1.affectations == ["aff:1"]
    assert a2.affectations == ["aff:2"]
    assert a3.affectations == ["aff:3"]

    assert a1.etat_jours == ["etat:1"]
    assert a2.etat_jours == ["etat:2"]
    assert a3.etat_jours == ["etat:3"]

    assert a1.qualifications == ["qualif:1"]
    assert a2.qualifications == ["qualif:2"]
    assert a3.qualifications == ["qualif:3"]

    agent_repo.list_all.assert_called_once_with()
    assert regime_repo.get_by_id.call_count == 2
    assert affectation_repo.list_for_agent.call_count == 3
    assert etat_repo.list_for_agent.call_count == 3
    assert qualification_repo.list_for_agent.call_count == 3


def test_list_agents_complets_liste_vide(service, repos):
    _, agent_repo, *rest = repos
    agent_repo.list_all.return_value = []

    result = service.list_agents_complets()

    assert result == []
    agent_repo.list_all.assert_called_once_with()
    # aucun autre repo ne doit être appelé
    for repo in rest:
        repo.assert_not_called()
