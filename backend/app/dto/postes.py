from pydantic import BaseModel
from typing import List

from backend.app.dto.tranches import TrancheDTO
from backend.app.dto.qualifications import QualificationDTO  # déjà créé chez toi

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
