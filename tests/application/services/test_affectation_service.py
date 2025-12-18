from datetime import date
from typing import Optional

from core.application.services.affectation_service import AffectationService


# ---------------------------------------------------------------------
# Fakes pour les tests
# ---------------------------------------------------------------------


class DummyAffectation:
    """Mini version d'Affectation pour tester le service sans dépendre du domaine complet."""

    def __init__(self, agent_id: int, tranche_id: int):
        self.agent_id = agent_id
        self.tranche_id = tranche_id
        self.agent = None
        self.tranche = None

    def set_agent(self, agent):
        self.agent = agent

    def set_tranche(self, tranche):
        self.tranche = tranche

    def __repr__(self):
        return f"DummyAffectation(agent_id={self.agent_id}, tranche_id={self.tranche_id})"


class FakeAffectationRepo:
    def __init__(self):
        self.list_all_result = []
        self.list_for_agent_args = []
        self.list_for_day_args = []
        self.list_for_poste_args = []
        self.get_for_agent_and_day_args = []
        self.get_for_agent_and_day_result = None

    def list_all(self):
        return self.list_all_result

    def list_for_agent(self, agent_id: int):
        self.list_for_agent_args.append(agent_id)
        # pour simplifier, on retourne une liste distincte pour vérifier
        return [DummyAffectation(agent_id=agent_id, tranche_id=1)]

    def list_for_day(self, jour):
        self.list_for_day_args.append(jour)
        return [DummyAffectation(agent_id=1, tranche_id=2)]

    def list_for_poste(self, poste_id: int, start: Optional[date] = None, end: Optional[date] = None):
        self.list_for_poste_args.append(poste_id)
        return [DummyAffectation(agent_id=2, tranche_id=3)]

    def get_for_agent_and_day(self, agent_id: int, jour: date):
        self.get_for_agent_and_day_args.append((agent_id, jour))
        return self.get_for_agent_and_day_result


class FakeAgentRepo:
    def __init__(self):
        self.get_args = []

    def get(self, agent_id: int):
        self.get_args.append(agent_id)
        return {"type": "agent", "id": agent_id}


class FakeTrancheRepo:
    def __init__(self):
        self.get_args = []

    def get(self, tranche_id: int):
        self.get_args.append(tranche_id)
        return {"type": "tranche", "id": tranche_id}


# ---------------------------------------------------------------------
# Tests de délégation simples
# ---------------------------------------------------------------------


def test_list_affectations_delegates_to_repo():
    repo = FakeAffectationRepo()
    repo.list_all_result = [
        DummyAffectation(agent_id=1, tranche_id=10),
        DummyAffectation(agent_id=2, tranche_id=20),
    ]
    service = AffectationService(
        affectation_repo=repo,
        agent_repo=FakeAgentRepo(),
        tranche_repo=FakeTrancheRepo(),
    )

    result = service.list_affectations()

    assert result is repo.list_all_result
    assert len(result) == 2


def test_list_for_agent_delegates_and_filters_by_agent():
    repo = FakeAffectationRepo()
    service = AffectationService(
        affectation_repo=repo,
        agent_repo=FakeAgentRepo(),
        tranche_repo=FakeTrancheRepo(),
    )

    result = service.list_for_agent(agent_id=42)

    # Le repo a bien reçu l'ID
    assert repo.list_for_agent_args == [42]
    # Le résultat vient bien du repo
    assert len(result) == 1
    assert result[0].agent_id == 42


def test_list_for_day_delegates_to_repo():
    repo = FakeAffectationRepo()
    service = AffectationService(
        affectation_repo=repo,
        agent_repo=FakeAgentRepo(),
        tranche_repo=FakeTrancheRepo(),
    )

    jour = date(2025, 1, 1)
    result = service.list_for_day(jour)

    assert repo.list_for_day_args == [jour]
    assert len(result) == 1
    assert isinstance(result[0], DummyAffectation)


def test_list_for_poste_delegates_to_repo():
    repo = FakeAffectationRepo()
    service = AffectationService(
        affectation_repo=repo,
        agent_repo=FakeAgentRepo(),
        tranche_repo=FakeTrancheRepo(),
    )

    result = service.list_for_poste(poste_id=7, start=None, end=None)

    assert repo.list_for_poste_args == [7]
    assert len(result) == 1
    assert isinstance(result[0], DummyAffectation)


# ---------------------------------------------------------------------
# Tests sur get_affectation_complet
# ---------------------------------------------------------------------


def test_get_affectation_complet_returns_none_if_repo_returns_none():
    repo = FakeAffectationRepo()
    repo.get_for_agent_and_day_result = None
    agent_repo = FakeAgentRepo()
    tranche_repo = FakeTrancheRepo()

    service = AffectationService(
        affectation_repo=repo,
        agent_repo=agent_repo,
        tranche_repo=tranche_repo,
    )

    jour = date(2025, 1, 1)
    result = service.get_affectation_complet(agent_id=99, jour=jour)

    assert result is None
    # Dans ce cas, on n'appelle pas les autres repos
    assert agent_repo.get_args == []
    assert tranche_repo.get_args == []


def test_get_affectation_complet_enriches_affectation():
    repo = FakeAffectationRepo()
    agent_repo = FakeAgentRepo()
    tranche_repo = FakeTrancheRepo()

    aff = DummyAffectation(agent_id=123, tranche_id=456)
    repo.get_for_agent_and_day_result = aff # pyright: ignore[reportAttributeAccessIssue]

    service = AffectationService(
        affectation_repo=repo,
        agent_repo=agent_repo,
        tranche_repo=tranche_repo,
    )

    jour = date(2025, 3, 15)
    result = service.get_affectation_complet(agent_id=123, jour=jour)

    # On récupère bien l'affectation du repo
    assert result is aff

    # Les repos Agent / Tranche ont été appelés avec les bons IDs
    assert agent_repo.get_args == [123]
    assert tranche_repo.get_args == [456]

    # Et l'affectation a bien été enrichie via set_agent / set_tranche
    assert aff.agent == {"type": "agent", "id": 123}
    assert aff.tranche == {"type": "tranche", "id": 456}


# ---------------------------------------------------------------------
# Tests sur list_affectations_completes
# ---------------------------------------------------------------------


def test_list_affectations_completes_enriches_all_affectations():
    repo = FakeAffectationRepo()
    agent_repo = FakeAgentRepo()
    tranche_repo = FakeTrancheRepo()

    aff1 = DummyAffectation(agent_id=1, tranche_id=10)
    aff2 = DummyAffectation(agent_id=2, tranche_id=20)
    repo.list_all_result = [aff1, aff2]

    service = AffectationService(
        affectation_repo=repo,
        agent_repo=agent_repo,
        tranche_repo=tranche_repo,
    )

    result = service.list_affectations_completes()

    # On retourne bien toutes les affectations
    assert result == [aff1, aff2]

    # Chaque affectation a été enrichie
    assert aff1.agent == {"type": "agent", "id": 1}
    assert aff1.tranche == {"type": "tranche", "id": 10}
    assert aff2.agent == {"type": "agent", "id": 2}
    assert aff2.tranche == {"type": "tranche", "id": 20}

    # Et les repos ont été appelés avec les bons IDs
    assert sorted(agent_repo.get_args) == [1, 2]
    assert sorted(tranche_repo.get_args) == [10, 20]
