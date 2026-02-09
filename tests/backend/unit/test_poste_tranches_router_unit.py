from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_tranche_service
from backend.app.api.deps_current_user import current_user

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakeTrancheService:
    def list_by_poste_id(self, poste_id: int):
        raise ValueError("Poste not found")


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


def test_list_tranches_for_poste_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_tranche_service] = lambda: _FakeTrancheService()

    r = client.get(f"{API}/postes/123/tranches")
    assert r.status_code == 404, r.text
    assert "Poste not found" in r.text
