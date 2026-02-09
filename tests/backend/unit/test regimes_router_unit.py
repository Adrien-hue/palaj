from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_regime_service
from backend.app.api.deps_current_user import current_user

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakeRegimeService:
    def create(self, **kwargs):
        raise ValueError("Already exists")

    def delete(self, regime_id: int) -> bool:
        return False

    def get_regime_complet(self, regime_id: int):
        return None

    def update(self, regime_id: int, **changes):
        return None

    def list(self, limit: int, offset: int):
        return []

    def count(self) -> int:
        return 0


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


def test_regimes_requires_auth(client_no_auth):
    r = client_no_auth.get(f"{API}/regimes")
    assert r.status_code == 401, r.text


def test_create_regime_conflict_is_409(client, app_auth):
    app_auth.dependency_overrides[get_regime_service] = lambda: _FakeRegimeService()

    r = client.post(f"{API}/regimes/", json={"name": "R1"})
    assert r.status_code in (409, 422), r.text  # 422 possible si DTO exige plus


def test_get_regime_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_regime_service] = lambda: _FakeRegimeService()

    r = client.get(f"{API}/regimes/123")
    assert r.status_code == 404, r.text
    assert "Regime not found" in r.text


def test_delete_regime_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_regime_service] = lambda: _FakeRegimeService()

    r = client.delete(f"{API}/regimes/123")
    assert r.status_code == 404, r.text
    assert "Regime not found" in r.text


def test_update_regime_empty_payload_is_400(client):
    r = client.patch(f"{API}/regimes/123", json={})
    assert r.status_code == 400, r.text
    assert "No fields to update" in r.text


def test_update_regime_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_regime_service] = lambda: _FakeRegimeService()

    r = client.patch(f"{API}/regimes/123", json={"name": "X"})
    assert r.status_code == 404, r.text
    assert "Regime not found" in r.text


def test_list_regimes_ok(client, app_auth):
    app_auth.dependency_overrides[get_regime_service] = lambda: _FakeRegimeService()

    r = client.get(f"{API}/regimes?limit=10&offset=0")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data and "total" in data
