# db/repositories/poste_repo.py
from datetime import date
from sqlalchemy import func, select

from db import db
from db.models import (
    Poste as PosteModel,
    Tranche as TrancheModel,
    PosteCoverageRequirement as PosteCoverageRequirementModel,
    AgentDayAssignment as AgentDayAssignmentModel,
    AgentDay as AgentDayModel
)

from core.domain.entities import Poste as PosteEntity
from core.application.read_models.poste_coverage_day_rm import TrancheCoverageRM
from db.sql_repository import SQLRepository
from core.adapters.entity_mapper import EntityMapper

class PosteRepository(SQLRepository[PosteModel, PosteEntity]):
    def __init__(self):
        super().__init__(db, PosteModel, PosteEntity)

    def _default_order_by(self):
        return (PosteModel.nom.asc(), PosteModel.id.asc())

    def get_by_id(self, poste_id: int) -> PosteEntity | None:
        """
        Récupère un poste par son ID.
        """
        return self.get(poste_id)

    def get_by_name(self, nom: str) -> PosteEntity | None:
        with self.db.session_scope() as session:
            model = (
                session.query(PosteModel)
                .filter(func.lower(PosteModel.nom) == nom.lower())
                .first()
            )
            return EntityMapper.model_to_entity(model, PosteEntity) if model else None
        
    def get_coverage_for_day(self, *, poste_id: int, day_date: date) -> list[TrancheCoverageRM]:
        """
        Retourne la couverture détaillée (par tranche) d'un poste pour une date donnée.

        - required_count: PosteCoverageRequirement(poste_id + weekday + tranche)
        - assigned_count: nombre d'affectations (AgentDayAssignment) sur la date pour la tranche
        """
        weekday = day_date.weekday()  # 0=lundi..6=dimanche

        with self.db.session_scope() as session:
            # Subquery: affectations comptées par tranche pour cette date
            assigned_sq = (
                select(
                    AgentDayAssignmentModel.tranche_id.label("tranche_id"),
                    func.count(AgentDayAssignmentModel.id).label("assigned_count"),
                )
                .select_from(AgentDayAssignmentModel)
                .join(AgentDayModel, AgentDayModel.id == AgentDayAssignmentModel.agent_day_id)
                .where(AgentDayModel.day_date == day_date)
                .group_by(AgentDayAssignmentModel.tranche_id)
                .subquery()
            )

            # Query principale : requirements + tranche, join sur assigned (left)
            stmt = (
                select(
                    TrancheModel.id.label("tranche_id"),
                    TrancheModel.nom.label("tranche_nom"),
                    TrancheModel.heure_debut,
                    TrancheModel.heure_fin,
                    PosteCoverageRequirementModel.required_count.label("required_count"),
                    func.coalesce(assigned_sq.c.assigned_count, 0).label("assigned_count"),
                )
                .select_from(PosteCoverageRequirementModel)
                .join(TrancheModel, TrancheModel.id == PosteCoverageRequirementModel.tranche_id)
                .outerjoin(assigned_sq, assigned_sq.c.tranche_id == TrancheModel.id)
                .where(PosteCoverageRequirementModel.poste_id == poste_id)
                .where(PosteCoverageRequirementModel.weekday == weekday)
                .order_by(TrancheModel.heure_debut.asc())
            )

            rows = session.execute(stmt).all()

            return [
                TrancheCoverageRM(
                    tranche_id=r.tranche_id,
                    tranche_nom=r.tranche_nom,
                    heure_debut=r.heure_debut,
                    heure_fin=r.heure_fin,
                    required_count=int(r.required_count),
                    assigned_count=int(r.assigned_count),
                )
                for r in rows
            ]