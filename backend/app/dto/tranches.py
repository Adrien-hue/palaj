from typing import Optional
from pydantic import BaseModel, Field
from datetime import time

class TrancheDTO(BaseModel):
    id: int
    nom: str
    heure_debut: time
    heure_fin: time
    poste_id: int

class TrancheCreateDTO(BaseModel):
    nom: str = Field(..., min_length=1, max_length=50)
    heure_debut: time
    heure_fin: time
    poste_id: int

class TrancheUpdateDTO(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=50)
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    poste_id: Optional[int] = None