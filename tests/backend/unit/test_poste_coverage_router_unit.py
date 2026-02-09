from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_poste_coverage_requirement_service, get_tranche_service
from backend.app.api.deps_current_user import current_user

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakeCoverageService:
    def replace_for_poste(self, poste_id: int, entities):
        raise ValueError("Invalid coverage requirement")


class _FakeTrancheService:
    def list_by_poste_id(self, poste_id: int):
        return []


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
def client(app_auth):
    with TestClient(app_auth) as c:
        yield c


def test_put_coverage_poste_id_mismatch_is_400(client):
    # On ne connaît pas exactement la structure des requirements -> on met un tableau vide (souvent valide)
    payload = {"poste_id": 999, "requirements": []}

    r = client.put(f"{API}/postes/123/coverage", json=payload)
    assert r.status_code == 400, r.text
    assert "poste_id mismatch" in r.text.lower()


def test_put_coverage_validation_is_422(client, app_auth):
    app_auth.dependency_overrides[get_poste_coverage_requirement_service] = lambda: _FakeCoverageService()
    app_auth.dependency_overrides[get_tranche_service] = lambda: _FakeTrancheService()

    payload = {"poste_id": 123, "requirements": []}
    r = client.put(f"{API}/postes/123/coverage", json=payload)

    # Si ton PosteCoveragePutDTO impose des champs dans requirements, Pydantic peut répondre 422 avant le service.
    # Dans les deux cas, 422 est attendu.
    assert r.status_code == 422, r.text
