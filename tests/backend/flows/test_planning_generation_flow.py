from __future__ import annotations

from contextlib import contextmanager
from datetime import date, time, timedelta
from importlib.util import find_spec
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.app.services.planning.generation import PlanningGenerationService
from backend.app.services.solver.models import TimeoutError
from backend.app.services.solver.ortools_solver import OrtoolsSolver
from backend.app.settings import settings
from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import (
    Agent,
    AgentTeam,
    PlanningDraft,
    PlanningDraftAgentDay,
    PlanningDraftAssignment,
    Poste,
    PosteCoverageRequirement,
    Qualification,
    Team,
    Tranche,
)

pytestmark = [pytest.mark.flow, pytest.mark.integration]

API = "/api/v1"
HTTPX_MISSING = find_spec("httpx") is None


class _TestDbAdapter:
    def __init__(self, bind):
        self._session_factory = sessionmaker(bind=bind, expire_on_commit=False, autoflush=False, autocommit=False)

    @contextmanager
    def session_scope(self):
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def _build_generation_service(db_session: Session) -> PlanningGenerationService:
    return PlanningGenerationService(solver=OrtoolsSolver(), database=_TestDbAdapter(db_session.get_bind()))


def _login(client, username: str, password: str):
    r = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    assert settings.access_cookie_name in client.cookies
    assert settings.refresh_cookie_name in client.cookies


def _seed_team(db_session: Session, agent_count: int = 1) -> Team:
    team = Team(name=f"Team planning draft {uuid4()}", description=None)
    db_session.add(team)
    db_session.flush()

    for idx in range(agent_count):
        agent = Agent(
            actif=True,
            nom=f"Doe-{idx}",
            prenom="Jane",
            code_personnel=f"A-{idx}",
            regime_id=None,
        )
        db_session.add(agent)
        db_session.flush()
        db_session.add(AgentTeam(agent_id=agent.id, team_id=team.id))

    db_session.commit()
    return team


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_post_generate_returns_job_and_draft(client, db_session: Session):
    _login(client, "admin", "admin123")
    team = _seed_team(db_session)

    payload = {
        "team_id": team.id,
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=3)),
        "seed": 123,
        "time_limit_seconds": 45,
    }
    r = client.post(f"{API}/planning/generate", json=payload)

    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == PlanningDraftStatus.QUEUED.value
    assert isinstance(data["job_id"], str)
    assert isinstance(data["draft_id"], int)


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_get_generate_status_unknown_job_returns_404(client):
    _login(client, "admin", "admin123")
    r = client.get(f"{API}/planning/generate/{uuid4()}")
    assert r.status_code == 404, r.text


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_get_generate_status_invalid_job_id_returns_422(client):
    _login(client, "admin", "admin123")
    r = client.get(f"{API}/planning/generate/not-a-uuid")
    assert r.status_code == 422, r.text


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_post_generate_invalid_dates_returns_422(client):
    _login(client, "admin", "admin123")

    payload = {
        "team_id": 1,
        "start_date": "2026-01-10",
        "end_date": "2026-01-01",
    }
    r = client.post(f"{API}/planning/generate", json=payload)
    assert r.status_code == 422, r.text




@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_get_generate_status_returns_result_stats_when_failed(client, db_session: Session, monkeypatch):
    _login(client, "admin", "admin123")
    team = _seed_team(db_session, agent_count=1)

    def _raise_timeout(self, _solver_input):
        raise TimeoutError(
            "timeout",
            stats={
                "solver_status": "UNKNOWN",
                "solver_status_raw": "UNKNOWN",
                "normalized_solver_status": "TIMEOUT",
                "is_timeout": True,
            },
        )

    monkeypatch.setattr(OrtoolsSolver, "generate", _raise_timeout)

    payload = {
        "team_id": team.id,
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "seed": 123,
        "time_limit_seconds": 1,
    }

    post_response = client.post(f"{API}/planning/generate", json=payload)
    assert post_response.status_code == 200, post_response.text
    job_id = post_response.json()["job_id"]

    status_response = client.get(f"{API}/planning/generate/{job_id}")
    assert status_response.status_code == 200, status_response.text

    data = status_response.json()
    assert data["status"] == PlanningDraftStatus.FAILED.value
    assert data["error"] is not None
    assert data["result_stats"] is not None
    assert set(data["result_stats"].keys()) == {"result_stats_schema_version", "stats"}
    assert data["result_stats"]["result_stats_schema_version"] == 3
    assert data["result_stats"]["stats"]["coverage"]["coverage_ratio"] == 0



@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_get_generate_status_normalizes_mixed_result_stats_payload(client, db_session: Session):
    _login(client, "admin", "admin123")
    team = _seed_team(db_session, agent_count=1)

    draft = PlanningDraft(
        job_id=str(uuid4()),
        team_id=team.id,
        start_date=date.today(),
        end_date=date.today(),
        status=PlanningDraftStatus.FAILED.value,
        time_limit_seconds=1,
        error="boom",
        result_stats={
            "result_stats_schema_version": 2,
            "stats": {
                "meta": {},
                "timing": {},
                "model": {},
                "coverage": {"coverage_ratio": 0},
                "objective": {},
                "solution_quality": {},
                "lns": {},
                "cp_sat": {},
            },
            "absence_count": 0,
            "demand_count": 12,
        },
    )
    db_session.add(draft)
    db_session.commit()

    response = client.get(f"{API}/planning/generate/{draft.job_id}")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["result_stats"] is not None
    assert set(payload["result_stats"].keys()) == {"result_stats_schema_version", "stats"}
    assert payload["result_stats"]["result_stats_schema_version"] == 3
    assert payload["result_stats"]["stats"]["coverage"]["coverage_ratio"] == 0

def test_runner_execution_with_string_job_id_sets_success_and_creates_agent_days_without_http_client(db_session: Session):
    team = _seed_team(db_session, agent_count=2)
    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 3)

    generation_service = _build_generation_service(db_session)

    draft = generation_service.create_draft(
        session=db_session,
        team_id=team.id,
        start_date=start_date,
        end_date=end_date,
        seed=123,
        time_limit_seconds=60,
    )
    db_session.commit()

    generation_service.run_job(str(draft.job_id))

    db_session.expire_all()
    persisted_draft = db_session.get(PlanningDraft, draft.id)
    assert persisted_draft is not None
    assert persisted_draft.status == PlanningDraftStatus.SUCCESS.value
    assert persisted_draft.result_stats is not None

    agent_ids = [
        agent_id
        for (agent_id,) in db_session.query(AgentTeam.agent_id).filter(AgentTeam.team_id == team.id).all()
    ]
    expected_days_count = len(agent_ids) * ((end_date - start_date).days + 1)
    created_days_count = (
        db_session.query(PlanningDraftAgentDay)
        .filter(PlanningDraftAgentDay.draft_id == persisted_draft.id)
        .count()
    )
    assignments_count = (
        db_session.query(PlanningDraftAssignment)
        .join(
            PlanningDraftAgentDay,
            PlanningDraftAgentDay.id == PlanningDraftAssignment.draft_agent_day_id,
        )
        .filter(PlanningDraftAgentDay.draft_id == persisted_draft.id)
        .count()
    )

    assert created_days_count == expected_days_count
    assert assignments_count == 0




def test_runner_marks_timeout_when_solver_times_out(db_session: Session, monkeypatch):
    team = _seed_team(db_session, agent_count=1)
    start_date = date(2026, 1, 5)
    end_date = date(2026, 1, 5)

    generation_service = _build_generation_service(db_session)

    def _raise_timeout(self, _solver_input):
        raise TimeoutError("timeout", stats={"solver_status": "UNKNOWN", "solver_status_raw": "UNKNOWN", "normalized_solver_status": "TIMEOUT", "is_timeout": True})

    monkeypatch.setattr(OrtoolsSolver, "generate", _raise_timeout)

    draft = generation_service.create_draft(
        session=db_session,
        team_id=team.id,
        start_date=start_date,
        end_date=end_date,
        seed=999,
        time_limit_seconds=1,
    )
    db_session.commit()

    generation_service.run_job(str(draft.job_id))

    db_session.expire_all()
    persisted_draft = db_session.get(PlanningDraft, draft.id)
    assert persisted_draft is not None
    assert persisted_draft.status == PlanningDraftStatus.FAILED.value
    assert persisted_draft.error == "timeout"
    assert persisted_draft.result_stats is not None
    assert persisted_draft.result_stats["solver_status"] == "TIMEOUT"
    assert persisted_draft.result_stats["coverage_ratio"] == 0
    assert persisted_draft.result_stats["solver_status_raw"] == "UNKNOWN"

def test_runner_adds_hard_infeasible_stats_for_unreachable_demand(db_session: Session):
    team = _seed_team(db_session, agent_count=1)
    start_date = date(2026, 1, 5)
    end_date = date(2026, 1, 5)

    agent_id = db_session.query(AgentTeam.agent_id).filter(AgentTeam.team_id == team.id).one()[0]

    poste = Poste(nom=f"Poste infeasible {uuid4()}")
    db_session.add(poste)
    db_session.flush()

    tranche = Tranche(
        nom=f"Tranche infeasible {uuid4()}",
        heure_debut=time(8, 0),
        heure_fin=time(12, 0),
        poste_id=poste.id,
        color=None,
    )
    db_session.add(tranche)
    db_session.flush()

    db_session.add(Qualification(agent_id=agent_id, poste_id=poste.id))
    db_session.add(
        PosteCoverageRequirement(
            poste_id=poste.id,
            weekday=start_date.weekday(),
            tranche_id=tranche.id,
            required_count=2,
        )
    )
    db_session.commit()

    generation_service = _build_generation_service(db_session)

    draft = generation_service.create_draft(
        session=db_session,
        team_id=team.id,
        start_date=start_date,
        end_date=end_date,
        seed=321,
        time_limit_seconds=30,
    )
    db_session.commit()

    generation_service.run_job(str(draft.job_id))

    db_session.expire_all()
    persisted_draft = db_session.get(PlanningDraft, draft.id)
    assert persisted_draft is not None
    assert persisted_draft.status == PlanningDraftStatus.FAILED.value
    assert persisted_draft.error == "infeasible"
    assert persisted_draft.result_stats is not None
    assert persisted_draft.result_stats["solver_status"] == "INFEASIBLE"
    assert persisted_draft.result_stats["coverage_ratio"] == 0
    coverage_constraints_count = persisted_draft.result_stats.get("coverage_constraints_count")
    if coverage_constraints_count is None:
        coverage_constraints_count = persisted_draft.result_stats["stats"]["model"].get("coverage_constraints_count")
    assert coverage_constraints_count is not None and coverage_constraints_count >= 0
    num_variables = persisted_draft.result_stats.get("num_variables")
    if num_variables is None:
        num_variables = persisted_draft.result_stats["stats"]["model"].get("num_variables")
    assert num_variables is not None and num_variables >= 0

    total_required_work_minutes = persisted_draft.result_stats.get("total_required_work_minutes")
    if total_required_work_minutes is None:
        total_required_work_minutes = persisted_draft.result_stats["stats"]["coverage"].get("total_required_count")
    assert total_required_work_minutes is not None and total_required_work_minutes > 0
    assert persisted_draft.result_stats["hard_infeasible_demands_count"] == 1
    assert persisted_draft.result_stats["ignored_coverage_requirements_count"] == 0
    assert persisted_draft.result_stats["covered_poste_ids_count"] == 1
    assert persisted_draft.result_stats["ignored_poste_ids_sample"] == []

    sample = persisted_draft.result_stats["hard_infeasible_demands_sample"]
    assert isinstance(sample, list)
    assert len(sample) == 1
    assert sample[0]["tranche_id"] == tranche.id
    assert sample[0]["required_count"] == 2
    assert sample[0]["capacity"] == 1


def test_runner_adds_ignored_coverage_requirement_stats(db_session: Session):
    team = _seed_team(db_session, agent_count=1)
    start_date = date(2026, 1, 5)
    end_date = date(2026, 1, 5)

    uncovered_poste = Poste(nom=f"Poste uncovered {uuid4()}")
    db_session.add(uncovered_poste)
    db_session.flush()

    uncovered_tranche = Tranche(
        nom=f"Tranche uncovered {uuid4()}",
        heure_debut=time(13, 0),
        heure_fin=time(17, 0),
        poste_id=uncovered_poste.id,
        color=None,
    )
    db_session.add(uncovered_tranche)
    db_session.flush()

    db_session.add(
        PosteCoverageRequirement(
            poste_id=uncovered_poste.id,
            weekday=start_date.weekday(),
            tranche_id=uncovered_tranche.id,
            required_count=1,
        )
    )
    db_session.commit()

    generation_service = _build_generation_service(db_session)
    draft = generation_service.create_draft(
        session=db_session,
        team_id=team.id,
        start_date=start_date,
        end_date=end_date,
        seed=42,
        time_limit_seconds=30,
    )
    db_session.commit()

    generation_service.run_job(str(draft.job_id))

    db_session.expire_all()
    persisted_draft = db_session.get(PlanningDraft, draft.id)
    assert persisted_draft is not None
    assert persisted_draft.status == PlanningDraftStatus.SUCCESS.value
    assert persisted_draft.result_stats is not None
    assert persisted_draft.result_stats["covered_poste_ids_count"] == 0
    assert persisted_draft.result_stats["ignored_coverage_requirements_count"] >= 1
    assert uncovered_poste.id in persisted_draft.result_stats["ignored_poste_ids_sample"]


def test_run_job_populates_existing_assignments_context_in_solver_input(db_session: Session, monkeypatch):
    team = _seed_team(db_session, agent_count=1)
    start_date = date(2026, 1, 10)
    end_date = date(2026, 1, 10)

    agent_id = db_session.query(AgentTeam.agent_id).filter(AgentTeam.team_id == team.id).one()[0]
    poste = Poste(nom=f"Poste existing {uuid4()}")
    db_session.add(poste)
    db_session.flush()
    tranche = Tranche(nom=f"Tranche existing {uuid4()}", heure_debut=time(8, 0), heure_fin=time(12, 0), poste_id=poste.id, color=None)
    db_session.add(tranche)
    db_session.flush()
    db_session.add(Qualification(agent_id=agent_id, poste_id=poste.id, date_qualification=None))
    db_session.add(PosteCoverageRequirement(poste_id=poste.id, weekday=start_date.weekday(), tranche_id=tranche.id, required_count=0))
    db_session.flush()

    from db.models import AgentDay, AgentDayAssignment

    existing_day = AgentDay(agent_id=agent_id, day_date=start_date, day_type="working", description=None, is_off_shift=False)
    db_session.add(existing_day)
    db_session.flush()
    db_session.add(AgentDayAssignment(agent_day_id=existing_day.id, tranche_id=tranche.id))
    db_session.commit()

    captured = {}
    original_generate = OrtoolsSolver.generate

    def _capture_generate(self, solver_input):
        captured["solver_input"] = solver_input
        return original_generate(self, solver_input)

    monkeypatch.setattr(OrtoolsSolver, "generate", _capture_generate)

    generation_service = _build_generation_service(db_session)
    draft = generation_service.create_draft(
        session=db_session,
        team_id=team.id,
        start_date=start_date,
        end_date=end_date,
        seed=42,
        time_limit_seconds=5,
    )
    db_session.commit()

    generation_service.run_job(str(draft.job_id))

    solver_input = captured["solver_input"]
    assert solver_input.use_existing_assignments is True
    assert solver_input.existing_daytype_by_agent_day_ctx[(agent_id, start_date)] == "working"
    existing_assignment = solver_input.existing_assignment_by_agent_day_ctx[(agent_id, start_date)]
    assert existing_assignment["poste_id"] == poste.id
    assert existing_assignment["tranche_ids"] == (tranche.id,)
