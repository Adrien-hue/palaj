from __future__ import annotations

from typing import List

from core.adapters.entity_mapper import EntityMapper
from db import db

from core.domain.entities.poste_coverage_requirement import PosteCoverageRequirement as PosteCoverageRequirementEntity

from db.models.poste_coverage_requirement import PosteCoverageRequirement as PosteCoverageRequirementModel
from db.sql_repository import SQLRepository


class PosteCoverageRequirementRepository(SQLRepository[PosteCoverageRequirementModel, PosteCoverageRequirementEntity]):
    def __init__(self):
        super().__init__(db, PosteCoverageRequirementModel, PosteCoverageRequirementEntity)

    def list_for_poste(self, poste_id: int) -> List[PosteCoverageRequirementEntity]:
        with self.db.session_scope() as session:
            models = (
                session.query(PosteCoverageRequirementModel)
                .filter(PosteCoverageRequirementModel.poste_id == poste_id)
                .order_by(
                    PosteCoverageRequirementModel.weekday.asc(),
                    PosteCoverageRequirementModel.tranche_id.asc(),
                )
                .all()
            )

            return [
                e for m in models
                if (e := EntityMapper.model_to_entity(m, PosteCoverageRequirementEntity)) is not None
            ]

    def replace_for_poste(self, poste_id: int, reqs: list[PosteCoverageRequirementEntity]) -> None:
        with self.db.session_scope() as session:
            (
                session.query(PosteCoverageRequirementModel)
                .filter(PosteCoverageRequirementModel.poste_id == poste_id)
                .delete(synchronize_session=False)
            )

            if reqs:
                session.add_all(
                    [
                        PosteCoverageRequirementModel(
                            poste_id=poste_id,
                            weekday=r.weekday,
                            tranche_id=r.tranche_id,
                            required_count=r.required_count,
                        )
                        for r in reqs
                    ]
                )

            session.flush()