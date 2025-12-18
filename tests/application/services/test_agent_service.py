from core.application.services.agent_service import AgentService


# ---------------------------------------------------------------------
# Fakes / helpers
# ---------------------------------------------------------------------


class DummyAgent:
    """Mini Agent métier, avec les setters utilisés par AgentService."""

    def __init__(self, id: int, regime_id=None):
        self.id = id
        self.regime_id = regime_id

        self.regime = None
        self.affectations = None
        self.etat_jours = None
        self.qualifications = None

    def set_regime(self, regime):
        self.regime = regime

    def set_affectations(self, affectations):
        self.affectations = affectations

    def set_etat_jours(self, etat_jours):
        self.etat_jours = etat_jours

    def set_qualifications(self, qualifications):
        self.qualifications = qualifications


class FakeAgentRepo:
    def __init__(self):
        self.list_all_result = []
        self.get_calls = []

    def list_all(self):
        return self.list_all_result

    def get(self, agent_id: int):
        self.get_calls.append(agent_id)
        # par défaut, on cherche dans list_all_result
        for a in self.list_all_result:
            if a.id == agent_id:
                return a
        return None


class FakeRegimeRepo:
    def __init__(self):
        self.get_calls = []

    def get(self, regime_id: int):
        self.get_calls.append(regime_id)
        return {"type": "regime", "id": regime_id}


class FakeAffectationRepo:
    def __init__(self):
        self.calls = []

    def list_for_agent(self, agent_id: int):
        self.calls.append(agent_id)
        return [{"type": "affectation", "agent_id": agent_id}]


class FakeEtatJourAgentRepo:
    def __init__(self):
        self.calls = []

    def list_for_agent(self, agent_id: int):
        self.calls.append(agent_id)
        return [{"type": "etat_jour", "agent_id": agent_id}]


class FakeQualificationRepo:
    def __init__(self):
        self.calls = []

    def list_for_agent(self, agent_id: int):
        self.calls.append(agent_id)
        return [{"type": "qualification", "agent_id": agent_id}]


# ---------------------------------------------------------------------
# Tests: méthodes simples
# ---------------------------------------------------------------------


def test_list_all_delegates_to_repo():
    agent_repo = FakeAgentRepo()
    agent_repo.list_all_result = [DummyAgent(1), DummyAgent(2)]

    service = AgentService(
        agent_repo=agent_repo,
        affectation_repo=FakeAffectationRepo(),
        etat_jour_agent_repo=FakeEtatJourAgentRepo(),
        regime_repo=FakeRegimeRepo(),
        qualification_repo=FakeQualificationRepo(),
    )

    result = service.list_all()

    assert result is agent_repo.list_all_result
    assert len(result) == 2


def test_get_delegates_to_repo_and_returns_agent_or_none():
    agent_repo = FakeAgentRepo()
    a1 = DummyAgent(10)
    agent_repo.list_all_result = [a1]

    service = AgentService(
        agent_repo=agent_repo,
        affectation_repo=FakeAffectationRepo(),
        etat_jour_agent_repo=FakeEtatJourAgentRepo(),
        regime_repo=FakeRegimeRepo(),
        qualification_repo=FakeQualificationRepo(),
    )

    found = service.get(10)
    missing = service.get(999)

    assert found is a1
    assert missing is None
    assert agent_repo.get_calls == [10, 999]


# ---------------------------------------------------------------------
# Tests: get_agent_complet
# ---------------------------------------------------------------------


def test_get_agent_complet_returns_none_if_agent_not_found():
    agent_repo = FakeAgentRepo()

    affect_repo = FakeAffectationRepo()
    etat_repo = FakeEtatJourAgentRepo()
    regime_repo = FakeRegimeRepo()
    qualif_repo = FakeQualificationRepo()

    service = AgentService(
        agent_repo=agent_repo,
        affectation_repo=affect_repo,
        etat_jour_agent_repo=etat_repo,
        regime_repo=regime_repo,
        qualification_repo=qualif_repo,
    )

    result = service.get_agent_complet(agent_id=123)

    assert result is None
    # aucun appel aux autres repos
    assert regime_repo.get_calls == []
    assert affect_repo.calls == []
    assert etat_repo.calls == []
    assert qualif_repo.calls == []


def test_get_agent_complet_enriches_agent_with_all_relations_when_regime_present():
    agent_repo = FakeAgentRepo()
    agent = DummyAgent(id=1, regime_id=42)
    agent_repo.list_all_result = [agent]

    affect_repo = FakeAffectationRepo()
    etat_repo = FakeEtatJourAgentRepo()
    regime_repo = FakeRegimeRepo()
    qualif_repo = FakeQualificationRepo()

    service = AgentService(
        agent_repo=agent_repo,
        affectation_repo=affect_repo,
        etat_jour_agent_repo=etat_repo,
        regime_repo=regime_repo,
        qualification_repo=qualif_repo,
    )

    result = service.get_agent_complet(agent_id=1)

    assert result is agent

    # Régime chargé
    assert regime_repo.get_calls == [42]
    assert agent.regime == {"type": "regime", "id": 42}

    # Affectations / états / qualifications chargés
    assert affect_repo.calls == [1]
    assert etat_repo.calls == [1]
    assert qualif_repo.calls == [1]

    assert agent.affectations == [{"type": "affectation", "agent_id": 1}]
    assert agent.etat_jours == [{"type": "etat_jour", "agent_id": 1}]
    assert agent.qualifications == [{"type": "qualification", "agent_id": 1}]


def test_get_agent_complet_does_not_load_regime_when_regime_id_is_falsy():
    agent_repo = FakeAgentRepo()
    agent = DummyAgent(id=2, regime_id=None)  # regime_id falsy
    agent_repo.list_all_result = [agent]

    affect_repo = FakeAffectationRepo()
    etat_repo = FakeEtatJourAgentRepo()
    regime_repo = FakeRegimeRepo()
    qualif_repo = FakeQualificationRepo()

    service = AgentService(
        agent_repo=agent_repo,
        affectation_repo=affect_repo,
        etat_jour_agent_repo=etat_repo,
        regime_repo=regime_repo,
        qualification_repo=qualif_repo,
    )

    result = service.get_agent_complet(agent_id=2)

    assert result is agent
    assert regime_repo.get_calls == []  # pas de chargement régime
    assert agent.regime is None

    # le reste est quand même chargé
    assert affect_repo.calls == [2]
    assert etat_repo.calls == [2]
    assert qualif_repo.calls == [2]


# ---------------------------------------------------------------------
# Tests: list_agents_complets
# ---------------------------------------------------------------------


def test_list_agents_complets_enriches_all_agents_and_loads_regime_conditionally():
    agent_repo = FakeAgentRepo()
    a1 = DummyAgent(id=1, regime_id=10)
    a2 = DummyAgent(id=2, regime_id=None)
    a3 = DummyAgent(id=3, regime_id=20)
    agent_repo.list_all_result = [a1, a2, a3]

    affect_repo = FakeAffectationRepo()
    etat_repo = FakeEtatJourAgentRepo()
    regime_repo = FakeRegimeRepo()
    qualif_repo = FakeQualificationRepo()

    service = AgentService(
        agent_repo=agent_repo,
        affectation_repo=affect_repo,
        etat_jour_agent_repo=etat_repo,
        regime_repo=regime_repo,
        qualification_repo=qualif_repo,
    )

    result = service.list_agents_complets()

    assert result == [a1, a2, a3]

    # Régime chargé uniquement pour a1 et a3
    assert regime_repo.get_calls == [10, 20]
    assert a1.regime == {"type": "regime", "id": 10}
    assert a2.regime is None
    assert a3.regime == {"type": "regime", "id": 20}

    # Affectations / états / qualifications pour tous
    assert affect_repo.calls == [1, 2, 3]
    assert etat_repo.calls == [1, 2, 3]
    assert qualif_repo.calls == [1, 2, 3]

    assert a2.affectations == [{"type": "affectation", "agent_id": 2}]
    assert a2.etat_jours == [{"type": "etat_jour", "agent_id": 2}]
    assert a2.qualifications == [{"type": "qualification", "agent_id": 2}]
