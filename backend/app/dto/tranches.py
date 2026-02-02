import re
from datetime import time
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class TrancheBaseDTO(BaseModel):
    nom: str = Field(..., min_length=1, max_length=50)
    heure_debut: time
    heure_fin: time
    poste_id: int
    color: Optional[str] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not HEX_COLOR_RE.match(v):
            raise ValueError("color must be a hex string like #RRGGBB")
        return v.upper()


class TrancheDTO(TrancheBaseDTO):
    model_config = ConfigDict(from_attributes=True)
    id: int


class TrancheCreateDTO(TrancheBaseDTO):
    pass


class TrancheUpdateDTO(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=50)
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    poste_id: Optional[int] = None
    color: Optional[str] = None

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not HEX_COLOR_RE.match(v):
            raise ValueError("color must be a hex string like #RRGGBB")
        return v.upper()
