from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_tranche_service
from backend.app.api.deps_current_user import current_user

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakeTrancheService:
    def get_by_id(self, tranche_id: int):
        return None

    def create(self, **kwargs):
        raise ValueError("Overlap rule")

    def update(self, tranche_id: int, **changes):
        return None

    def delete(self, tranche_id: int) -> bool:
        return False

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


def test_tranches_requires_auth(client_no_auth):
    r = client_no_auth.get(f"{API}/tranches")
    assert r.status_code == 401, r.text


def test_get_tranche_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_tranche_service] = lambda: _FakeTrancheService()

    r = client.get(f"{API}/tranches/123")
    assert r.status_code == 404, r.text
    assert "Tranche not found" in r.text


def test_create_tranche_conflict_is_409(client, app_auth):
    app_auth.dependency_overrides[get_tranche_service] = lambda: _FakeTrancheService()

    r = client.post(f"{API}/tranches/", json={"name": "T1"})
    assert r.status_code in (409, 422), r.text  # 422 possible si DTO impose plus


def test_update_tranche_empty_payload_is_400(client):
    r = client.patch(f"{API}/tranches/123", json={})
    assert r.status_code == 400, r.text
    assert "No fields to update" in r.text


def test_update_tranche_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_tranche_service] = lambda: _FakeTrancheService()

    r = client.patch(f"{API}/tranches/123", json={"name": "X"})
    assert r.status_code == 404, r.text


def test_delete_tranche_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_tranche_service] = lambda: _FakeTrancheService()

    r = client.delete(f"{API}/tranches/123")
    assert r.status_code == 404, r.text
    assert "Tranche not found" in r.text


def test_list_tranches_ok(client, app_auth):
    app_auth.dependency_overrides[get_tranche_service] = lambda: _FakeTrancheService()

    r = client.get(f"{API}/tranches?limit=10&offset=0")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data and "total" in data
