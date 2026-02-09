from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_poste_service
from backend.app.api.deps_current_user import current_user

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakePosteService:
    def get_poste_complet(self, poste_id: int):
        return None  # force 404

    def delete(self, poste_id: int) -> bool:
        return False  # force 404

    def update(self, poste_id: int, **changes):
        return None  # force 404


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


def test_postes_requires_auth(client_no_auth):
    r = client_no_auth.get(f"{API}/postes")
    assert r.status_code == 401, r.text


def test_get_poste_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_poste_service] = lambda: _FakePosteService()

    r = client.get(f"{API}/postes/123")
    assert r.status_code == 404, r.text
    assert "Poste not found" in r.text


def test_delete_poste_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_poste_service] = lambda: _FakePosteService()

    r = client.delete(f"{API}/postes/123")
    assert r.status_code == 404, r.text
    assert "Poste not found" in r.text


def test_delete_poste_conflict_is_409(client, app_auth):
    class _Fake(_FakePosteService):
        def delete(self, poste_id: int) -> bool:
            raise ValueError("Poste linked to tranches")

    app_auth.dependency_overrides[get_poste_service] = lambda: _Fake()

    r = client.delete(f"{API}/postes/123")
    assert r.status_code == 409, r.text
    assert "linked" in r.text.lower()


def test_update_poste_empty_payload_is_400(client, app_auth):
    # pas besoin d’override service : l’erreur arrive avant l’appel
    r = client.patch(f"{API}/postes/123", json={})
    assert r.status_code == 400, r.text
    assert "No fields to update" in r.text


def test_update_poste_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_poste_service] = lambda: _FakePosteService()

    r = client.patch(f"{API}/postes/123", json={"name": "X"})
    assert r.status_code == 404, r.text
    assert "Poste not found" in r.text
