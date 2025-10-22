from models.poste import Poste

from db.base_repository import BaseRepository

from utils.text_utils import normalize_text

class PosteRepository(BaseRepository[Poste]):
    def __init__(self, db):
        super().__init__(db, "postes", Poste)

    def _serialize(self, obj: Poste) -> dict:
        return obj.to_dict()

    def _deserialize(self, data: dict) -> Poste:
        tranche_ids = data.get("tranches", [])

        return Poste(
            id=data["id"],
            nom=data["nom"],
            tranche_ids=tranche_ids
        )

    def get_by_name(self, nom: str) -> list[Poste]:
        """
        Recherche un ou plusieurs postes par nom.
        Insensible à la casse et aux accents.

        :param nom: Nom du poste à rechercher
        :return: Liste de postes correspondants ou [] si aucun
        """
        nom_normalized = normalize_text(nom)
        results = []

        # --- Recherche dans le cache ---
        for poste in self._cache.values():
            if normalize_text(poste.nom) == nom_normalized:
                results.append(poste)

        if results:
            self.cache_manager.register_hit("Poste")
            return results

        # --- Sinon, recherche dans la BDD ---
        all_data = self.list_all()
        for data in all_data:
            if normalize_text(data.nom) == nom_normalized:
                self._cache_set(str(data.id), data)
                results.append(data)

        if results:
            self.cache_manager.register_miss("Poste")

        return results
