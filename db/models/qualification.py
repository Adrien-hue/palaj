# db/models/qualification.py
from sqlalchemy import Column, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Qualification(Base):
    __tablename__ = "qualifications"
    __table_args__ = (UniqueConstraint("agent_id", "poste_id", name="_qualification_uc"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    poste_id = Column(Integer, ForeignKey("postes.id"), nullable=False)
    date_qualification = Column(Date, nullable=True)

    agent = relationship("Agent", back_populates="qualifications")
    poste = relationship("Poste", back_populates="qualifications")

    def __repr__(self):
        return f"<Qualification agent={self.agent_id} poste={self.poste_id}>"
