from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
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

    regime: Optional["RegimeDTO"] = None
    qualifications: List["QualificationDTO"] = Field(default_factory=list)


class AgentUpdateDTO(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    code_personnel: Optional[str] = Field(default=None, max_length=50)
    regime_id: Optional[int] = None
    actif: Optional[bool] = None
