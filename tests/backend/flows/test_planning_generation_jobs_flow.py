from __future__ import annotations

from datetime import date, datetime, timedelta
from importlib.util import find_spec
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import PlanningDraft, Team

pytestmark = [pytest.mark.flow, pytest.mark.integration]

API = "/api/v1"
HTTPX_MISSING = find_spec("httpx") is None


def _login(client, username: str, password: str):
    response = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _create_team(db_session: Session, name: str) -> Team:
    team = Team(name=name, description=None)
    db_session.add(team)
    db_session.flush()
    return team


def _create_job(
    db_session: Session,
    *,
    team_id: int,
    status: PlanningDraftStatus,
    created_at: datetime,
    start_date: date | None = None,
    end_date: date | None = None,
) -> PlanningDraft:
    start = start_date or date(2026, 3, 1)
    end = end_date or date(2026, 3, 31)
    draft = PlanningDraft(
        job_id=str(uuid4()),
        team_id=team_id,
        start_date=start,
        end_date=end,
        status=status.value,
        seed=123,
        time_limit_seconds=30,
        created_at=created_at,
        updated_at=created_at,
    )
    db_session.add(draft)
    db_session.flush()
    return draft


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_list_generation_jobs_returns_paginated_recent_first(client, db_session: Session):
    _login(client, "admin", "admin123")

    team_a = _create_team(db_session, f"Team A {uuid4()}")
    team_b = _create_team(db_session, f"Team B {uuid4()}")
    base_time = datetime(2026, 3, 6, 10, 0, 0)

    first = _create_job(db_session, team_id=team_a.id, status=PlanningDraftStatus.QUEUED, created_at=base_time)
    second = _create_job(
        db_session,
        team_id=team_b.id,
        status=PlanningDraftStatus.RUNNING,
        created_at=base_time + timedelta(minutes=1),
    )
    third = _create_job(
        db_session,
        team_id=team_a.id,
        status=PlanningDraftStatus.SUCCESS,
        created_at=base_time + timedelta(minutes=2),
    )
    db_session.commit()

    response = client.get(f"{API}/planning/generate/jobs", params={"page": 1, "page_size": 2})

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert payload["total"] == 3
    assert len(payload["items"]) == 2

    assert payload["items"][0]["job_id"] == third.job_id
    assert payload["items"][1]["job_id"] == second.job_id
    assert payload["items"][0]["team_name"] == team_a.name
    assert payload["items"][1]["team_name"] == team_b.name

    page_2 = client.get(f"{API}/planning/generate/jobs", params={"page": 2, "page_size": 2})
    assert page_2.status_code == 200, page_2.text
    page_2_payload = page_2.json()
    assert len(page_2_payload["items"]) == 1
    assert page_2_payload["items"][0]["job_id"] == first.job_id


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_list_generation_jobs_filters_by_status(client, db_session: Session):
    _login(client, "admin", "admin123")

    team = _create_team(db_session, f"Team Status {uuid4()}")
    created_at = datetime(2026, 3, 6, 9, 0, 0)

    _create_job(db_session, team_id=team.id, status=PlanningDraftStatus.SUCCESS, created_at=created_at)
    failed = _create_job(
        db_session,
        team_id=team.id,
        status=PlanningDraftStatus.FAILED,
        created_at=created_at + timedelta(minutes=1),
    )
    db_session.commit()

    response = client.get(f"{API}/planning/generate/jobs", params={"status": PlanningDraftStatus.FAILED.value})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["job_id"] == failed.job_id
    assert payload["items"][0]["status"] == PlanningDraftStatus.FAILED.value


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_list_generation_jobs_filters_by_team(client, db_session: Session):
    _login(client, "admin", "admin123")

    team_a = _create_team(db_session, f"Team Filter A {uuid4()}")
    team_b = _create_team(db_session, f"Team Filter B {uuid4()}")
    created_at = datetime(2026, 3, 6, 11, 0, 0)

    _create_job(db_session, team_id=team_a.id, status=PlanningDraftStatus.SUCCESS, created_at=created_at)
    kept = _create_job(
        db_session,
        team_id=team_b.id,
        status=PlanningDraftStatus.QUEUED,
        created_at=created_at + timedelta(minutes=1),
    )
    db_session.commit()

    response = client.get(f"{API}/planning/generate/jobs", params={"team_id": team_b.id})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["job_id"] == kept.job_id
    assert payload["items"][0]["team_id"] == team_b.id


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_list_generation_jobs_search_by_job_id(client, db_session: Session):
    _login(client, "admin", "admin123")

    team = _create_team(db_session, f"Team Search {uuid4()}")
    created_at = datetime(2026, 3, 6, 12, 0, 0)
    to_find = _create_job(db_session, team_id=team.id, status=PlanningDraftStatus.SUCCESS, created_at=created_at)
    _create_job(
        db_session,
        team_id=team.id,
        status=PlanningDraftStatus.SUCCESS,
        created_at=created_at + timedelta(minutes=1),
    )
    db_session.commit()

    search_fragment = to_find.job_id.split("-")[0]
    response = client.get(f"{API}/planning/generate/jobs", params={"search": search_fragment})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["job_id"] == to_find.job_id


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_list_generation_jobs_admin_only(client, db_session: Session):
    team = _create_team(db_session, f"Team Auth {uuid4()}")
    _create_job(
        db_session,
        team_id=team.id,
        status=PlanningDraftStatus.QUEUED,
        created_at=datetime(2026, 3, 6, 13, 0, 0),
    )
    db_session.commit()

    _login(client, "user", "user123")

    response = client.get(f"{API}/planning/generate/jobs")

    assert response.status_code == 403, response.text


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_list_generation_jobs_search_numeric_matches_draft_id_and_job_id_text(client, db_session: Session):
    _login(client, "admin", "admin123")

    team = _create_team(db_session, f"Team Numeric Search {uuid4()}")
    created_at = datetime(2026, 3, 7, 10, 0, 0)

    draft_id_match = _create_job(
        db_session,
        team_id=team.id,
        status=PlanningDraftStatus.SUCCESS,
        created_at=created_at,
    )
    search_token = str(draft_id_match.id)
    # keep a deterministic numeric token in the UUID string so job_id textual search also matches.
    job_id_match = PlanningDraft(
        job_id=f"00000000-0000-0000-0000-{int(search_token):012d}",
        team_id=team.id,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        status=PlanningDraftStatus.SUCCESS.value,
        seed=321,
        time_limit_seconds=30,
        created_at=created_at + timedelta(minutes=1),
        updated_at=created_at + timedelta(minutes=1),
    )
    db_session.add(job_id_match)
    db_session.commit()

    response = client.get(f"{API}/planning/generate/jobs", params={"search": search_token})

    assert response.status_code == 200, response.text
    payload = response.json()
    returned_ids = {item["draft_id"] for item in payload["items"]}

    assert draft_id_match.id in returned_ids
    assert job_id_match.id in returned_ids


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_list_generation_jobs_combines_status_and_team_filters(client, db_session: Session):
    _login(client, "admin", "admin123")

    team_a = _create_team(db_session, f"Team Combo A {uuid4()}")
    team_b = _create_team(db_session, f"Team Combo B {uuid4()}")
    created_at = datetime(2026, 3, 7, 11, 0, 0)

    expected = _create_job(
        db_session,
        team_id=team_a.id,
        status=PlanningDraftStatus.SUCCESS,
        created_at=created_at,
    )
    _create_job(
        db_session,
        team_id=team_a.id,
        status=PlanningDraftStatus.FAILED,
        created_at=created_at + timedelta(minutes=1),
    )
    _create_job(
        db_session,
        team_id=team_b.id,
        status=PlanningDraftStatus.SUCCESS,
        created_at=created_at + timedelta(minutes=2),
    )
    db_session.commit()

    response = client.get(
        f"{API}/planning/generate/jobs",
        params={"status": PlanningDraftStatus.SUCCESS.value, "team_id": team_a.id},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["draft_id"] == expected.id


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_list_generation_jobs_created_to_date_is_inclusive_for_whole_day(client, db_session: Session):
    _login(client, "admin", "admin123")

    team = _create_team(db_session, f"Team Created To {uuid4()}")
    day = datetime(2026, 3, 8, 0, 0, 0)

    included = _create_job(
        db_session,
        team_id=team.id,
        status=PlanningDraftStatus.SUCCESS,
        created_at=day.replace(hour=23, minute=59, second=59),
    )
    _create_job(
        db_session,
        team_id=team.id,
        status=PlanningDraftStatus.SUCCESS,
        created_at=day + timedelta(days=1),
    )
    db_session.commit()

    response = client.get(f"{API}/planning/generate/jobs", params={"created_to": "2026-03-08"})

    assert response.status_code == 200, response.text
    payload = response.json()
    returned_ids = {item["draft_id"] for item in payload["items"]}
    assert included.id in returned_ids
