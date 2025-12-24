from pydantic import BaseModel, Field
from typing import List, Optional

from backend.app.dto.affectations import AffectationDTO
from backend.app.dto.etats_jours_agents import EtatJourAgentDTO
from backend.app.dto.qualifications import QualificationDTO
from backend.app.dto.regimes import RegimeDTO

class AgentCreateDTO(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    code_personnel: str = Field(default="", max_length=50)
    regime_id: Optional[int] = None
    actif: bool = True

class AgentDTO(BaseModel):
    id: int
    nom: str
    prenom: str
    code_personnel: Optional[str] = None
    actif: bool = True

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

class AgentUpdateDTO(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    code_personnel: Optional[str] = Field(default=None, max_length=50)
    regime_id: Optional[int] = None
    actif: Optional[bool] = None