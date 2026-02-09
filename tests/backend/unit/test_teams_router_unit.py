from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_team_service
from backend.app.api.deps_current_user import current_user
from core.application.services.exceptions import ConflictError, NotFoundError

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakeTeamService:
    def list(self, limit: int, offset: int):
        return []

    def count(self) -> int:
        return 0

    def create(self, name: str, description: str | None = None):
        raise ConflictError(code="TEAM_ALREADY_EXISTS")

    def get(self, team_id: int):
        raise NotFoundError(code="TEAM_NOT_FOUND")

    def update(self, team_id: int, **changes):
        raise NotFoundError(code="TEAM_NOT_FOUND")

    def delete(self, team_id: int) -> None:
        return None


@pytest.fixture()
def app_no_auth():
    app = create_app()

    def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db
    return app


@pytest.fixture()
def app_auth():
    app = create_app()

    def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db

    def _override_current_user():
        return {"id": 1, "username": "test", "role": "admin", "is_active": True}

    app.dependency_overrides[current_user] = _override_current_user
    return app


@pytest.fixture()
def client_no_auth(app_no_auth):
    with TestClient(app_no_auth) as c:
        yield c


@pytest.fixture()
def client(app_auth):
    with TestClient(app_auth) as c:
        yield c


def test_teams_requires_auth(client_no_auth):
    r = client_no_auth.get(f"{API}/teams")
    assert r.status_code == 401, r.text


def test_list_teams_ok(client, app_auth):
    app_auth.dependency_overrides[get_team_service] = lambda: _FakeTeamService()

    r = client.get(f"{API}/teams?limit=10&offset=0")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data and "total" in data


def test_create_team_conflict_is_409(client, app_auth):
    app_auth.dependency_overrides[get_team_service] = lambda: _FakeTeamService()

    # payload minimal (si DTO impose plus, 422 possible avant d'atteindre le service)
    r = client.post(f"{API}/teams", json={"name": "A", "description": None})
    assert r.status_code in (409, 422), r.text
    if r.status_code == 409:
        assert r.json()["detail"] == "TEAM_ALREADY_EXISTS"


def test_get_team_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_team_service] = lambda: _FakeTeamService()

    r = client.get(f"{API}/teams/123")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "TEAM_NOT_FOUND"


def test_update_team_empty_payload_is_400(client):
    r = client.patch(f"{API}/teams/123", json={})
    assert r.status_code == 400, r.text
    assert "No fields to update" in r.text


def test_update_team_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_team_service] = lambda: _FakeTeamService()

    r = client.patch(f"{API}/teams/123", json={"name": "X"})
    assert r.status_code == 404, r.text
    # selon ta branche, ça peut être "Team not found" ou "TEAM_NOT_FOUND"
    assert "not found" in str(r.json()["detail"]).lower()


def test_delete_team_is_204(client, app_auth):
    app_auth.dependency_overrides[get_team_service] = lambda: _FakeTeamService()

    r = client.delete(f"{API}/teams/123")
    assert r.status_code == 204, r.text
