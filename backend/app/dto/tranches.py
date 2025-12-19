from pydantic import BaseModel
from datetime import time

class TrancheDTO(BaseModel):
    id: int
    nom: str
    heure_debut: time
    heure_fin: time
    poste_id: int