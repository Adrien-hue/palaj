from backend.app.dto.regimes import RegimeDTO
from core.domain.entities import Regime

def to_regime_dto(r: Regime) -> RegimeDTO:
    return RegimeDTO(
        id=r.id,
        nom=r.nom,
        desc=r.desc,

        min_rp_annuels=r.min_rp_annuels,
        min_rp_dimanches=r.min_rp_dimanches,

        min_rpsd=r.min_rpsd,
        min_rp_2plus=r.min_rp_2plus,

        min_rp_semestre=r.min_rp_semestre,

        avg_service_minutes=r.avg_service_minutes,
        avg_tolerance_minutes=r.avg_tolerance_minutes,
    )
