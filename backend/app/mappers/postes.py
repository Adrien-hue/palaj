from backend.app.dto.postes import PosteDTO, PosteDetailDTO
from backend.app.mappers.tranches import to_tranche_dto
from backend.app.mappers.qualifications import to_qualification_dto

def to_poste_list_item_dto(p) -> PosteDTO:
    return PosteDTO(id=p.id, nom=p.nom)

def to_poste_detail_dto(p) -> PosteDetailDTO:
    return PosteDetailDTO(
        id=p.id,
        nom=p.nom,
        tranches=[to_tranche_dto(t) for t in p.tranches],
        qualifications=[to_qualification_dto(q) for q in p.qualifications],
    )
