from backend.app.dto.tranches import TrancheDTO

def to_tranche_dto(t) -> TrancheDTO:
    return TrancheDTO(
        id=t.id,
        nom=t.nom,
        heure_debut=t.heure_debut,
        heure_fin=t.heure_fin,
        poste_id=t.poste_id,
    )
