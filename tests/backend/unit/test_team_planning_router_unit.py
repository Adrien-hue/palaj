from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import get_db, get_team_planning_factory
from backend.app.api.deps_current_user import current_user
from core.application.services.exceptions import NotFoundError

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakePlanningFactoryNotFound:
    def build(self, **kwargs):
        raise NotFoundError(code="TEAM_NOT_FOUND", details={"team_id": kwargs.get("team_id")})


class _FakePlanningFactoryBadRange:
    def build(self, **kwargs):
        raise ValueError("end_date must be >= start_date")


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


def test_team_planning_requires_auth(client_no_auth):
    today = date.today()
    r = client_no_auth.get(f"{API}/teams/1/planning?start_date={today}&end_date={today}")
    assert r.status_code == 401, r.text


def test_get_team_planning_not_found_is_404_structured_detail(client, app_auth):
    app_auth.dependency_overrides[get_team_planning_factory] = lambda: _FakePlanningFactoryNotFound()

    today = date.today()
    r = client.get(f"{API}/teams/123/planning?start_date={today}&end_date={today}")
    assert r.status_code == 404, r.text

    detail = r.json()["detail"]
    assert detail["code"] == "TEAM_NOT_FOUND"
    assert "details" in detail


def test_get_team_planning_invalid_range_is_400(client, app_auth):
    app_auth.dependency_overrides[get_team_planning_factory] = lambda: _FakePlanningFactoryBadRange()

    start = date.today()
    end = start - timedelta(days=1)
    r = client.get(f"{API}/teams/1/planning?start_date={start}&end_date={end}")
    assert r.status_code == 400, r.text
    assert "end_date" in r.text.lower()
