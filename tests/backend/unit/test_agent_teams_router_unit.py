from __future__ import annotations

from dataclasses import dataclass
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db
from backend.app.api.deps_current_user import current_user
from backend.app.api.deps import get_agent_team_service

from core.application.services.exceptions import NotFoundError


pytestmark = [pytest.mark.unit]

API = "/api/v1"


@dataclass
class _Membership:
    agent_id: int
    team_id: int


class _FakeAgentTeamService:
    def __init__(self):
        self.memberships: set[tuple[int, int]] = set()

    def create(self, agent_id: int, team_id: int) -> None:
        # Simule des erreurs "domain"
        if agent_id == 404 or team_id == 404:
            # NotFoundError doit avoir .code (comme dans ton router)
            raise NotFoundError(code="NOT_FOUND")
        key = (agent_id, team_id)
        if key in self.memberships:
            raise ValueError("Membership already exists")
        self.memberships.add(key)

    def delete(self, agent_id: int, team_id: int) -> bool:
        key = (agent_id, team_id)
        if key not in self.memberships:
            return False
        self.memberships.remove(key)
        return True

    def search(self, agent_id: int | None = None, team_id: int | None = None):
        items = []
        for a, t in sorted(self.memberships):
            if agent_id is not None and a != agent_id:
                continue
            if team_id is not None and t != team_id:
                continue
            items.append(_Membership(agent_id=a, team_id=t))
        return items


@pytest.fixture()
def app():
    """
    App isolée pour tests unitaires router:
    - override DB (on n'en a pas besoin ici)
    - override current_user (bypass auth)
    - override get_agent_team_service (fake)
    """
    app = create_app()

    # Neutralise get_db (au cas où)
    def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db

    # Bypass auth: le router est protégé par current_user au niveau include_router(...)
    def _override_current_user():
        return {"id": 1, "username": "test", "role": "admin", "is_active": True}

    app.dependency_overrides[current_user] = _override_current_user

    fake = _FakeAgentTeamService()
    app.dependency_overrides[get_agent_team_service] = lambda: fake

    return app


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c


def test_add_agent_team_201(client):
    r = client.post(f"{API}/agent-teams/1/10")
    assert r.status_code == 201, r.text


def test_add_agent_team_not_found_404(client):
    r = client.post(f"{API}/agent-teams/404/10")
    assert r.status_code == 404, r.text
    # ton router renvoie detail=e.code
    assert r.json()["detail"] == "NOT_FOUND"


def test_add_agent_team_conflict_409(client):
    r1 = client.post(f"{API}/agent-teams/1/10")
    assert r1.status_code == 201, r1.text

    r2 = client.post(f"{API}/agent-teams/1/10")
    assert r2.status_code == 409, r2.text
    assert "already exists" in r2.json()["detail"]


def test_delete_agent_team_204(client):
    client.post(f"{API}/agent-teams/1/10")

    r = client.delete(f"{API}/agent-teams/1/10")
    assert r.status_code == 204, r.text


def test_delete_agent_team_missing_is_404(client):
    r = client.delete(f"{API}/agent-teams/1/999")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "Membership not found"


def test_search_agent_teams_returns_filtered_list(client):
    client.post(f"{API}/agent-teams/1/10")
    client.post(f"{API}/agent-teams/1/11")
    client.post(f"{API}/agent-teams/2/10")

    r_all = client.get(f"{API}/agent-teams/")
    assert r_all.status_code == 200, r_all.text
    assert isinstance(r_all.json(), list)
    assert len(r_all.json()) == 3

    r_agent1 = client.get(f"{API}/agent-teams/?agent_id=1")
    assert r_agent1.status_code == 200, r_agent1.text
    assert len(r_agent1.json()) == 2

    r_team10 = client.get(f"{API}/agent-teams/?team_id=10")
    assert r_team10.status_code == 200, r_team10.text
    assert len(r_team10.json()) == 2
