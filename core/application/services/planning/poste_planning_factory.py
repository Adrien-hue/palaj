from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from core.domain.models.poste_planning import PostePlanning

if TYPE_CHECKING:
    from core.application.ports.poste_repo import PosteRepositoryPort
    from core.application.services.planning.poste_planning_day_assembler import PostePlanningDayAssembler


class PostePlanningFactory:
    def __init__(
        self,
        poste_repo: PosteRepositoryPort,
        planning_day_assembler: PostePlanningDayAssembler,
    ) -> None:
        self.poste_repo = poste_repo
        self.planning_day_assembler = planning_day_assembler

    def build(
        self,
        poste_id: int,
        start_date: date,
        end_date: date,
    ) -> PostePlanning:
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        poste = self.poste_repo.get_by_id(poste_id)
        if not poste:
            raise ValueError(f"Poste {poste_id} not found.")

        days = self.planning_day_assembler.build_for_poste(
            poste_id=poste_id,
            start_date=start_date,
            end_date=end_date,
        )

        return PostePlanning(
            poste=poste,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )
