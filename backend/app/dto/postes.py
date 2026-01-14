from pydantic import BaseModel, Field
from typing import List, Optional

from backend.app.dto.tranches import TrancheDTO
from backend.app.dto.qualifications import QualificationDTO

class PosteDTO(BaseModel):
    id: int
    nom: str

class PosteListDTO(BaseModel):
    items: List[PosteDTO]
    total: int

class PosteDetailDTO(BaseModel):
    id: int
    nom: str
    tranches: List[TrancheDTO] = []
    qualifications: List[QualificationDTO] = []

class PosteCreateDTO(BaseModel):
    nom: str = Field(..., min_length=1, max_length=100)

class PosteUpdateDTO(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=100)