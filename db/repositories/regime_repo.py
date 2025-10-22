from models.regime import Regime

from db.base_repository import BaseRepository

class RegimeRepository(BaseRepository[Regime]):
    def __init__(self, db):
        super().__init__(db, "regimes", Regime)

    def _serialize(self, obj: Regime) -> dict:
        return obj.to_dict()

    def _deserialize(self, data: dict) -> Regime:
        regime = Regime(
            id=data["id"],
            nom=data["nom"],
            desc=data.get("desc") or "",
            duree_moyenne_journee_service_min=data["duree_moyenne_journee_service_min"],
            repos_periodiques_annuels=data["repos_periodiques_annuels"],
        )

        return regime