from pydantic import BaseModel
from typing import List, Optional

from backend.app.dto.affectations import AffectationDTO
from backend.app.dto.etats_jours_agents import EtatJourAgentDTO
from backend.app.dto.qualifications import QualificationDTO
from backend.app.dto.regimes import RegimeDTO


class AgentDTO(BaseModel):
    id: int
    nom: str
    prenom: str
    code_personnel: Optional[str] = None
    actif: bool = True


class AgentListDTO(BaseModel):
    items: List[AgentDTO]
    total: int

class AgentDetailDTO(BaseModel):
    id: int
    nom: str
    prenom: str
    code_personnel: str = ""
    actif: bool
    regime_id: Optional[int] = None

    regime: Optional[RegimeDTO] = None
    qualifications: List[QualificationDTO] = []
    affectations: List[AffectationDTO] = []
    etat_jours: List[EtatJourAgentDTO] = []