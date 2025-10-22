from models.tranche import Tranche

from db.base_repository import BaseRepository

class TrancheRepository(BaseRepository[Tranche]):
    def __init__(self, db):
        super().__init__(db, "tranches", Tranche)

    def _serialize(self, obj: Tranche) -> dict:
        return obj.to_dict()

    def _deserialize(self, data: dict) -> Tranche:
        tranche = Tranche(
            id=data["id"],
            abbr=data["nom"],
            debut=data["heure_debut"],
            fin=data["heure_fin"],
            nb_agents_requis=data.get("nb_agents_requis", 1)
        )

        return tranche
    
    def get_by_name(self, abbr: str):
        """
        Récupère une tranche à partir de son nom (abbr).
        Cherche d'abord dans le cache, puis dans les fichiers JSON si nécessaire.
        """
        # --- Recherche dans le cache ---
        for tranche in self._cache.values():
            if tranche.abbr == abbr:
                self.cache_manager.register_hit("Tranche")
                return tranche

        # --- Recherche dans les fichiers si non trouvé ---
        all_data = self.list_all()
        for data in all_data:
            if data.abbr == abbr:
                self._cache_set(str(data.id), data)
                self.cache_manager.register_miss("Tranche")
                return data

        # Rien trouvé
        self.cache_manager.register_miss("Tranche")
        return None
