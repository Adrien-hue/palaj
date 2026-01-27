# db/repositories/__init__.py
from db.repositories.agent_repo import AgentRepository
from db.repositories.agent_day_repo import AgentDayRepository
from db.repositories.agent_day_assignment_repo import AgentDayAssignmentRepository
from db.repositories.poste_repo import PosteRepository
from db.repositories.tranche_repo import TrancheRepository
from db.repositories.regime_repo import RegimeRepository
from db.repositories.qualification_repo import QualificationRepository
from db.repositories.agent_team_repo import AgentTeamSQLRepository
from db.repositories.team_repo import TeamSQLRepository

agent_repo = AgentRepository()
agent_day_repo = AgentDayRepository()
agent_day_assignment_repo = AgentDayAssignmentRepository()
poste_repo = PosteRepository()
tranche_repo = TrancheRepository()
regime_repo = RegimeRepository()
qualification_repo = QualificationRepository()
agent_team_repo = AgentTeamSQLRepository()
team_repo = TeamSQLRepository()

__all__ = [
    "agent_repo",
    "agent_day_repo",
    "agent_day_assignment_repo",
    "poste_repo",
    "tranche_repo",
    "regime_repo",
    "qualification_repo",
    "agent_team_repo",
    "team_repo",
]