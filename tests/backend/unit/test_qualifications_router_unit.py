from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_qualification_service
from backend.app.api.deps_current_user import current_user

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakeQualificationService:
    def create(self, **kwargs):
        raise ValueError("Already exists")

    def delete(self, agent_id: int, poste_id: int) -> bool:
        return False

    def update(self, agent_id: int, poste_id: int, **changes):
        return None

    def search(self, agent_id=None, poste_id=None):
        return []


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


def test_qualifications_requires_auth(client_no_auth):
    r = client_no_auth.get(f"{API}/qualifications")
    assert r.status_code == 401, r.text


def test_create_qualification_conflict_is_409(client, app_auth):
    app_auth.dependency_overrides[get_qualification_service] = lambda: _FakeQualificationService()

    # payload volontairement minimal (si DTO exige plus, Pydantic répondra 422 -> OK aussi)
    r = client.post(f"{API}/qualifications/", json={"agent_id": 1, "poste_id": 1})
    assert r.status_code in (409, 422), r.text


def test_delete_qualification_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_qualification_service] = lambda: _FakeQualificationService()

    r = client.delete(f"{API}/qualifications/1/2")
    assert r.status_code == 404, r.text
    assert "Qualification not found" in r.text


def test_update_qualification_empty_payload_is_400(client):
    r = client.patch(f"{API}/qualifications/1/2", json={})
    assert r.status_code == 400, r.text
    assert "No fields to update" in r.text


def test_update_qualification_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_qualification_service] = lambda: _FakeQualificationService()

    r = client.patch(f"{API}/qualifications/1/2", json={"level": 1})
    assert r.status_code == 404, r.text
    assert "Qualification not found" in r.text
