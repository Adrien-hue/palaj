from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import (
    get_db,
    get_poste_planning_factory,
    get_poste_service,
    get_poste_planning_day_service,
)
from backend.app.api.deps_current_user import current_user
from core.application.services.exceptions import NotFoundError

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakePlanningFactory404:
    def build(self, **kwargs):
        raise ValueError("Poste not found")


class _FakePlanningFactory400:
    def build(self, **kwargs):
        raise ValueError("end_date must be >= start_date")


class _FakePosteServiceNotFound:
    def get_poste_coverage_for_day(self, **kwargs):
        raise NotFoundError(code="POSTE_NOT_FOUND", details={"poste_id": kwargs.get("poste_id")})


class _FakePostePlanningDayService:
    def delete_poste_day(self, **kwargs):
        raise ValueError("Invalid day")


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


def test_get_poste_planning_poste_not_found_is_404(client, app_auth):
    app_auth.dependency_overrides[get_poste_planning_factory] = lambda: _FakePlanningFactory404()

    start = date.today()
    end = start
    r = client.get(f"{API}/postes/123/planning?start_date={start}&end_date={end}")
    assert r.status_code == 404, r.text
    assert "poste not found" in r.text.lower()


def test_get_poste_planning_invalid_range_is_400(client, app_auth):
    app_auth.dependency_overrides[get_poste_planning_factory] = lambda: _FakePlanningFactory400()

    start = date.today()
    end = start - timedelta(days=1)
    r = client.get(f"{API}/postes/123/planning?start_date={start}&end_date={end}")
    assert r.status_code == 400, r.text
    assert "end_date" in r.text.lower()


def test_get_poste_planning_coverage_not_found_is_404_with_structured_detail(client, app_auth):
    app_auth.dependency_overrides[get_poste_service] = lambda: _FakePosteServiceNotFound()

    d = date.today()
    r = client.get(f"{API}/postes/123/planning/coverage?date={d}")
    assert r.status_code == 404, r.text
    detail = r.json()["detail"]
    assert detail["code"] == "POSTE_NOT_FOUND"
    assert "details" in detail


def test_delete_poste_day_value_error_is_400(client, app_auth):
    app_auth.dependency_overrides[get_poste_planning_day_service] = lambda: _FakePostePlanningDayService()

    d = date.today()
    r = client.delete(f"{API}/postes/123/planning/days/{d}")
    assert r.status_code == 400, r.text
    assert "invalid" in r.text.lower()
