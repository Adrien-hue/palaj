from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_agent_service
from backend.app.api.deps_current_user import current_user


pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakeAgentServiceBase:
    # endpoints utilisés dans ces tests uniquement
    def activate(self, agent_id: int) -> bool:
        return True

    def deactivate(self, agent_id: int) -> bool:
        return True

    def delete(self, agent_id: int) -> bool:
        return True

    def get_agent_complet(self, agent_id: int) -> dict | None:
        return {"id": agent_id}  # ne sera pas mappé dans les tests d'erreur

    def update(self, agent_id: int, **changes):
        return {"id": agent_id, **changes}


@pytest.fixture()
def app_no_auth():
    """
    App sans override current_user -> permet de tester le 401.
    """
    app = create_app()

    def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db
    return app


@pytest.fixture()
def app_auth():
    """
    App avec override current_user + fake AgentService.
    """
    app = create_app()

    def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db

    def _override_current_user():
        # le router est protégé au niveau include_router(dependencies=[Depends(current_user)])
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


def test_agents_requires_auth(client_no_auth):
    r = client_no_auth.get(f"{API}/agents")
    assert r.status_code == 401, r.text


def test_update_agent_empty_payload_is_400(client, app_auth):
    class _Fake(_FakeAgentServiceBase):
        pass

    app_auth.dependency_overrides[get_agent_service] = lambda: _Fake()

    r = client.patch(f"{API}/agents/1", json={})
    assert r.status_code == 400, r.text
    assert "No fields to update" in r.text


def test_get_agent_not_found_is_404(client, app_auth):
    class _Fake(_FakeAgentServiceBase):
        def get_agent_complet(self, agent_id: int):
            return None

    app_auth.dependency_overrides[get_agent_service] = lambda: _Fake()

    r = client.get(f"{API}/agents/9999")
    assert r.status_code == 404, r.text
    assert "Agent not found" in r.text


def test_activate_agent_not_found_is_404(client, app_auth):
    class _Fake(_FakeAgentServiceBase):
        def activate(self, agent_id: int) -> bool:
            return False

    app_auth.dependency_overrides[get_agent_service] = lambda: _Fake()

    r = client.patch(f"{API}/agents/9999/activate")
    assert r.status_code == 404, r.text
    assert "Agent not found" in r.text


def test_delete_agent_conflict_is_409(client, app_auth):
    class _Fake(_FakeAgentServiceBase):
        def delete(self, agent_id: int) -> bool:
            raise ValueError("Agent is referenced elsewhere")

    app_auth.dependency_overrides[get_agent_service] = lambda: _Fake()

    r = client.delete(f"{API}/agents/1")
    assert r.status_code == 409, r.text
    assert "referenced" in r.text.lower()
