from __future__ import annotations

from datetime import date
from uuid import uuid4

from backend.app.services.solver.mapper import CoverageRequirementPattern, SolverInputMapper
from db.models import Agent, AgentDay, AgentTeam, Poste, Qualification, Team


def _create_team_with_agents(db_session, count: int = 2) -> tuple[Team, list[Agent]]:
    team = Team(name=f"team-mapper-{uuid4()}", description=None)
    db_session.add(team)
    db_session.flush()

    agents: list[Agent] = []
    for idx in range(count):
        agent = Agent(
            actif=True,
            nom=f"Nom-{idx}",
            prenom=f"Prenom-{idx}",
            code_personnel=f"CP-{idx}",
            regime_id=None,
        )
        db_session.add(agent)
        db_session.flush()
        db_session.add(AgentTeam(agent_id=agent.id, team_id=team.id))
        agents.append(agent)

    db_session.flush()
    return team, agents


def test_expand_requirements_to_demands_expands_weekday_dates(db_session):
    mapper = SolverInputMapper(session=db_session)
    start_date = date(2026, 1, 5)  # monday
    end_date = date(2026, 1, 11)   # sunday

    requirements = [
        CoverageRequirementPattern(poste_id=10, weekday=0, tranche_id=100, required_count=2),
        CoverageRequirementPattern(poste_id=10, weekday=2, tranche_id=100, required_count=1),
    ]

    demands = mapper.expand_requirements_to_demands(
        requirements=requirements,
        start_date=start_date,
        end_date=end_date,
        existing_tranche_ids={100},
    )

    assert [(d.day_date, d.required_count) for d in demands] == [
        (date(2026, 1, 5), 2),
        (date(2026, 1, 7), 1),
    ]


def test_expand_requirements_to_demands_filters_unknown_tranche_ids(db_session):
    mapper = SolverInputMapper(session=db_session)

    demands = mapper.expand_requirements_to_demands(
        requirements=[
            CoverageRequirementPattern(poste_id=1, weekday=0, tranche_id=10, required_count=1),
            CoverageRequirementPattern(poste_id=1, weekday=0, tranche_id=11, required_count=3),
        ],
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 5),
        existing_tranche_ids={10},
    )

    assert len(demands) == 1
    assert demands[0].tranche_id == 10


def test_expand_requirements_to_demands_is_sorted_by_date_and_tranche(db_session):
    mapper = SolverInputMapper(session=db_session)

    demands = mapper.expand_requirements_to_demands(
        requirements=[
            CoverageRequirementPattern(poste_id=1, weekday=0, tranche_id=20, required_count=1),
            CoverageRequirementPattern(poste_id=1, weekday=0, tranche_id=10, required_count=1),
        ],
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 12),
        existing_tranche_ids={10, 20},
    )

    assert [(d.day_date, d.tranche_id) for d in demands] == [
        (date(2026, 1, 5), 10),
        (date(2026, 1, 5), 20),
        (date(2026, 1, 12), 10),
        (date(2026, 1, 12), 20),
    ]


def test_qualifications_builds_union_and_mapping(db_session):
    team, agents = _create_team_with_agents(db_session)

    poste_a = Poste(nom=f"Poste-A-{team.id}")
    poste_b = Poste(nom=f"Poste-B-{team.id}")
    db_session.add_all([poste_a, poste_b])
    db_session.flush()

    db_session.add_all(
        [
            Qualification(agent_id=agents[0].id, poste_id=poste_a.id),
            Qualification(agent_id=agents[0].id, poste_id=poste_b.id),
            Qualification(agent_id=agents[1].id, poste_id=poste_b.id),
        ]
    )
    db_session.commit()

    mapper = SolverInputMapper(session=db_session)
    agent_ids = mapper.list_team_agent_ids(team_id=team.id)
    qualified = mapper.list_qualified_postes_by_agent(agent_ids=agent_ids)
    poste_ids = mapper.list_team_poste_ids(qualified_postes_by_agent=qualified)

    assert qualified == {
        agents[0].id: {poste_a.id, poste_b.id},
        agents[1].id: {poste_b.id},
    }
    assert poste_ids == {poste_a.id, poste_b.id}


def test_list_absences_returns_only_absent_days(db_session):
    team, agents = _create_team_with_agents(db_session)

    db_session.add_all(
        [
            AgentDay(agent_id=agents[0].id, day_date=date(2026, 1, 5), day_type="absent"),
            AgentDay(agent_id=agents[0].id, day_date=date(2026, 1, 6), day_type="leave"),
            AgentDay(agent_id=agents[1].id, day_date=date(2026, 1, 7), day_type="absent"),
        ]
    )
    db_session.commit()

    mapper = SolverInputMapper(session=db_session)
    absences = mapper.list_absences(
        agent_ids=[agents[0].id, agents[1].id],
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 7),
    )

    assert absences == {
        (agents[0].id, date(2026, 1, 5)),
        (agents[1].id, date(2026, 1, 7)),
    }


def test_no_qualified_postes_yields_empty_tranches_requirements_and_demands(db_session):
    team, _agents = _create_team_with_agents(db_session)
    mapper = SolverInputMapper(session=db_session)

    agent_ids = mapper.list_team_agent_ids(team_id=team.id)
    qualified = mapper.list_qualified_postes_by_agent(agent_ids=agent_ids)
    poste_ids = mapper.list_team_poste_ids(qualified_postes_by_agent=qualified)
    tranches = mapper.list_tranches_for_postes(poste_ids=poste_ids)
    requirements = mapper.list_coverage_requirements(poste_ids=poste_ids)
    demands = mapper.expand_requirements_to_demands(
        requirements=requirements,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 2),
        existing_tranche_ids={tranche.id for tranche in tranches},
    )

    assert poste_ids == set()
    assert tranches == []
    assert requirements == []
    assert demands == []


def test_mapper_is_deterministic_for_demands_and_qualified_postes(db_session):
    team, agents = _create_team_with_agents(db_session)

    poste = Poste(nom=f"Poste-Det-{uuid4()}")
    db_session.add(poste)
    db_session.flush()

    db_session.add_all(
        [
            Qualification(agent_id=agents[0].id, poste_id=poste.id),
            Qualification(agent_id=agents[1].id, poste_id=poste.id),
        ]
    )
    db_session.commit()

    mapper = SolverInputMapper(session=db_session)

    agent_ids_1 = mapper.list_team_agent_ids(team_id=team.id)
    qualified_1 = mapper.list_qualified_postes_by_agent(agent_ids=agent_ids_1)
    normalized_1 = mapper.normalize_qualified_postes_by_agent(agent_ids_1, qualified_1)
    poste_ids_1 = mapper.list_team_poste_ids(qualified_postes_by_agent=qualified_1)
    requirements_1 = [
        CoverageRequirementPattern(poste_id=poste.id, weekday=0, tranche_id=100, required_count=1),
        CoverageRequirementPattern(poste_id=poste.id, weekday=2, tranche_id=100, required_count=1),
    ]
    demands_1 = mapper.expand_requirements_to_demands(
        requirements=requirements_1,
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 12),
        existing_tranche_ids={100},
    )

    agent_ids_2 = mapper.list_team_agent_ids(team_id=team.id)
    qualified_2 = mapper.list_qualified_postes_by_agent(agent_ids=agent_ids_2)
    normalized_2 = mapper.normalize_qualified_postes_by_agent(agent_ids_2, qualified_2)
    poste_ids_2 = mapper.list_team_poste_ids(qualified_postes_by_agent=qualified_2)
    requirements_2 = [
        CoverageRequirementPattern(poste_id=poste.id, weekday=0, tranche_id=100, required_count=1),
        CoverageRequirementPattern(poste_id=poste.id, weekday=2, tranche_id=100, required_count=1),
    ]
    demands_2 = mapper.expand_requirements_to_demands(
        requirements=requirements_2,
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 12),
        existing_tranche_ids={100},
    )

    assert agent_ids_1 == agent_ids_2
    assert normalized_1 == normalized_2
    assert poste_ids_1 == poste_ids_2
    assert demands_1 == demands_2
