from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.dto.agents import AgentDTO


class RegimeDTO(BaseModel):
    id: int
    nom: str
    desc: str = ""

    min_rp_annuels: Optional[int] = None
    min_rp_dimanches: Optional[int] = None

    min_rpsd: Optional[int] = None
    min_rp_2plus: Optional[int] = None

    min_rp_semestre: Optional[int] = None

    avg_service_minutes: Optional[int] = None
    avg_tolerance_minutes: Optional[int] = None


class RegimeDetailDTO(RegimeDTO):
    agents: List["AgentDTO"] = Field(default_factory=list)


class RegimeCreateDTO(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100)
    desc: str = Field(default="", max_length=1000)

    min_rp_annuels: Optional[int] = Field(None, ge=0)
    min_rp_dimanches: Optional[int] = Field(None, ge=0)

    min_rpsd: Optional[int] = Field(None, ge=0)
    min_rp_2plus: Optional[int] = Field(None, ge=0)

    min_rp_semestre: Optional[int] = Field(None, ge=0)

    avg_service_minutes: Optional[int] = Field(None, ge=0)
    avg_tolerance_minutes: Optional[int] = Field(None, ge=0)


class RegimeUpdateDTO(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    desc: Optional[str] = Field(None, max_length=1000)

    min_rp_annuels: Optional[int] = Field(None, ge=0)
    min_rp_dimanches: Optional[int] = Field(None, ge=0)

    min_rpsd: Optional[int] = Field(None, ge=0)
    min_rp_2plus: Optional[int] = Field(None, ge=0)

    min_rp_semestre: Optional[int] = Field(None, ge=0)

    avg_service_minutes: Optional[int] = Field(None, ge=0)
    avg_tolerance_minutes: Optional[int] = Field(None, ge=0)
