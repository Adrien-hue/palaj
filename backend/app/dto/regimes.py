from pydantic import BaseModel
from typing import List

class RegimeDTO(BaseModel):
    id: int
    nom: str
    desc: str = ""
    duree_moyenne_journee_service_min: int = 0
    repos_periodiques_annuels: int = 0

class RegimeListDTO(BaseModel):
    total: int
    regimes: List[RegimeDTO]

class RegimeDetailDTO(BaseModel):
    id: int
    nom: str
    desc: str
    duree_moyenne_journee_service_min: int
    repos_periodiques_annuels: int