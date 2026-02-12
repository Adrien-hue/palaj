# backend/app/bootstrap/container.py

from core.application.services import (
    AgentDayService,
    AgentService,
    AgentPlanningFactory,
    PlanningDayAssembler,
    PostePlanningFactory,
    PostePlanningDayAssembler,
    PostePlanningDayService,
    TeamPlanningFactory,
    PosteCoverageRequirementService,
    PosteService,
    QualificationService,
    RegimeService,
    AgentTeamService,
    TeamService,
    TrancheService,
)

from db.repositories import (
    agent_repo,
    agent_day_repo,
    agent_day_assignment_repo,
    poste_coverage_requirement_repo,
    poste_repo,
    qualification_repo,
    regime_repo,
    tranche_repo,
    agent_team_repo,
    team_repo,
)


# ---------------------------------------------------------
# Repositories -> Services
# ---------------------------------------------------------

agent_day_service = AgentDayService(
    agent_day_repo=agent_day_repo,
    assignment_repo=agent_day_assignment_repo,
)

agent_service = AgentService(
    agent_repo=agent_repo,
    agent_day_repo=agent_day_repo,
    qualification_repo=qualification_repo,
    regime_repo=regime_repo,
)

poste_service = PosteService(
    poste_repo=poste_repo,
    qualification_repo=qualification_repo,
    tranche_repo=tranche_repo,
)

poste_coverage_requirement_service = PosteCoverageRequirementService(
    repo=poste_coverage_requirement_repo
)

qualification_service = QualificationService(
    agent_repo=agent_repo,
    poste_repo=poste_repo,
    qualification_repo=qualification_repo,
)

regime_service = RegimeService(
    agent_repo=agent_repo,
    regime_repo=regime_repo,
)

tranche_service = TrancheService(
    poste_repo=poste_repo,
    tranche_repo=tranche_repo,
    agent_day_assignment_repo=agent_day_assignment_repo
)

team_service = TeamService(repo=team_repo)

agent_team_service = AgentTeamService(
    agent_repo=agent_repo,
    team_repo=team_repo,
    agent_team_repo=agent_team_repo
)

# ---------------------------------------------------------
# Planning
# ---------------------------------------------------------
planning_day_assembler = PlanningDayAssembler(
    agent_day_repo=agent_day_repo,
    tranche_repo=tranche_repo,
)

poste_planning_day_assembler = PostePlanningDayAssembler(
    tranche_repo=tranche_repo,
    agent_repo=agent_repo,
    agent_day_repo=agent_day_repo
)

poste_planning_day_service = PostePlanningDayService(
    tranche_repo=tranche_repo,
    agent_day_repo=agent_day_repo,
    agent_day_assignment_repo=agent_day_assignment_repo
)

agent_planning_factory = AgentPlanningFactory(
    agent_service=agent_service,
    planning_day_assembler=planning_day_assembler,
)

poste_planning_factory = PostePlanningFactory(
    poste_repo=poste_repo,
    planning_day_assembler=poste_planning_day_assembler
)

team_planning_factory = TeamPlanningFactory(
    team_service=team_service,
    agent_service=agent_service,
    planning_day_assembler=planning_day_assembler,
)

__all__ = [
    "agent_day_service",
    "agent_service",
    "poste_service",
    "poste_coverage_requirement_service",
    "qualification_service",
    "regime_service",
    "tranche_service",
    "planning_day_assembler",
    "agent_planning_factory",
    "poste_planning_factory",
    "poste_planning_day_assembler",
    "poste_planning_day_service",
    "team_planning_factory",
    "agent_team_service",
    "team_service",
]
