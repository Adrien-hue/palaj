from backend.app.dto.regimes import RegimeDTO

def to_regime_dto(regime) -> RegimeDTO:
    return RegimeDTO(
        id=regime.id,
        nom=regime.nom,
        desc=regime.desc,
        duree_moyenne_journee_service_min=regime.duree_moyenne_journee_service_min,
        repos_periodiques_annuels=regime.repos_periodiques_annuels,
    )
