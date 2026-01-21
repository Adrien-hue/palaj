from datetime import date

from core.application.ports.poste_repo import PosteRepositoryPort
from core.application.ports.tranche_repo import TrancheRepositoryPort
from core.application.ports.agent_repo import AgentRepositoryPort
from core.application.ports.agent_day_repo import AgentDayRepositoryPort

from core.domain.models.poste_planning import PostePlanning
from core.application.services.planning.poste_planning_day_assembler import PostePlanningDayAssembler

class PostePlanningFactory:
    def __init__(
        self,
        *,
        poste_repo: PosteRepositoryPort,
        tranche_repo: TrancheRepositoryPort,
        agent_repo: AgentRepositoryPort,
        agent_day_repo: AgentDayRepositoryPort,
        day_assembler: PostePlanningDayAssembler,
    ):
        self.poste_repo = poste_repo
        self.tranche_repo = tranche_repo
        self.agent_repo = agent_repo
        self.agent_day_repo = agent_day_repo
        self.day_assembler = day_assembler

    def build(self, *, poste_id: int, start_date: date, end_date: date) -> PostePlanning:
        if end_date < start_date:
            raise ValueError("end_date must be >= start_date")

        poste = self.poste_repo.get_by_id(poste_id)
        if not poste:
            raise ValueError("Poste not found")

        tranches = self.tranche_repo.list_by_poste_id(poste_id)
        tranches = sorted(tranches, key=lambda t: (t.heure_debut, t.heure_fin, t.id))

        agent_days = self.agent_day_repo.list_by_poste_and_range(
            poste_id=poste_id,
            start_date=start_date,
            end_date=end_date,
        )
        print(agent_days)
        agent_ids = sorted({ad.agent_id for ad in agent_days})
        agents = self.agent_repo.list_by_ids(agent_ids)
        agents_by_id = {a.id: a for a in agents}

        days = self.day_assembler.assemble(
            start_date=start_date,
            end_date=end_date,
            tranches=tranches,
            agents_by_id=agents_by_id,
            agent_days=agent_days,
        )

        return PostePlanning(
            poste=poste,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )
