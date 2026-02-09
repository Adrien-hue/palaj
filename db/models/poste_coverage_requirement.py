from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey, ForeignKeyConstraint, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .poste import Poste
    from .tranche import Tranche


class PosteCoverageRequirement(Base):
    __tablename__ = "poste_coverage_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)

    poste_id: Mapped[int] = mapped_column(
        ForeignKey("postes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    weekday: Mapped[int] = mapped_column(nullable=False)

    tranche_id: Mapped[int] = mapped_column(nullable=False, index=True)

    required_count: Mapped[int] = mapped_column(nullable=False, default=1)

    poste: Mapped["Poste"] = relationship(
        "Poste",
        back_populates="coverage_requirements",
        overlaps="tranche",
    )

    tranche: Mapped["Tranche"] = relationship(
        "Tranche",
        back_populates="coverage_requirements",
        overlaps="poste,coverage_requirements",
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["poste_id", "tranche_id"],
            ["tranches.poste_id", "tranches.id"],
            name="fk_pcr_poste_tranche",
            ondelete="CASCADE",
        ),
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_poste_coverage_weekday_range"),
        UniqueConstraint("poste_id", "weekday", "tranche_id", name="uq_poste_weekday_tranche"),
        Index("ix_poste_coverage_poste_weekday", "poste_id", "weekday"),
    )
