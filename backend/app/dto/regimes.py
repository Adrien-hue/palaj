from pydantic import BaseModel

class RegimeDTO(BaseModel):
    id: int
    nom: str
    desc: str = ""
    duree_moyenne_journee_service_min: int = 0
    repos_periodiques_annuels: int = 0
