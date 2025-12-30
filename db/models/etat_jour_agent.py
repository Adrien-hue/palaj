# db/models/etat_jour_agent.py
from sqlalchemy import Column, Date, ForeignKey, Integer, Text, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import relationship

from .base import Base
from .enums import TypeJourDB


class EtatJourAgent(Base):
    __tablename__ = "etat_jour_agent"
    __table_args__ = (UniqueConstraint("agent_id", "jour", name="_etat_jour_uc"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    jour = Column(Date, nullable=False)

    type_jour = Column(
        SAEnum(
            TypeJourDB,
            values_callable=lambda enum: [e.value for e in enum],  # store "conge" not "TypeJourDB.CONGE"
            name="type_jour_enum",
        ),
        nullable=False,
    )

    description = Column(Text, nullable=True)

    agent = relationship("Agent", back_populates="etats")

    def __repr__(self):
        return f"<EtatJourAgent agent={self.agent_id} jour={self.jour} type={self.type_jour}>"
