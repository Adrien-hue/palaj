# db/models/affectation.py
from sqlalchemy import Column, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Affectation(Base):
    __tablename__ = "affectations"
    __table_args__ = (UniqueConstraint("agent_id", "jour", "tranche_id", name="_affectation_uc"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    tranche_id = Column(Integer, ForeignKey("tranches.id"), nullable=False)
    jour = Column(Date, nullable=False)

    agent = relationship("Agent", back_populates="affectations")
    tranche = relationship("Tranche", back_populates="affectations")

    def __repr__(self):
        return f"<Affectation agent={self.agent_id} tranche={self.tranche_id} jour={self.jour}>"
