from __future__ import annotations

from db.base_repository import BaseRepository
from models.agent import Agent


from utils.text_utils import normalize_text

class AgentRepository(BaseRepository[Agent]):
    def __init__(self, db):
        super().__init__(db, "agents", Agent)

    def _serialize(self, obj: Agent) -> dict:
        return obj.to_dict()

    def _deserialize(self, data: dict) -> Agent:
        agent = Agent(
            id=data["id"],
            nom=data["nom"],
            prenom=data["prenom"],
            code_personnel=data.get("code_personnel") or "",
            regime_id=data.get("regime_id") or -1
        )

        return agent

    def get_by_name(self, nom: str | None = None, prenom: str | None = None) -> list[Agent]:
        """
        Recherche un agent par nom, prénom ou les deux.

        :param nom: Nom de famille de l'agent (insensible à la casse)
        :param prenom: Prénom de l'agent (insensible à la casse)
        :return: Liste d'agents correspondants ou [] si aucun résultat
        """
        results = []

        nom = normalize_text(nom)
        prenom = normalize_text(prenom)

        # --- Recherche dans le cache ---
        for agent in self._cache.values():
            if (
                (nom and prenom and normalize_text(agent.nom) == nom and normalize_text(agent.prenom) == prenom)
                or (nom and not prenom and normalize_text(agent.nom) == nom)
                or (prenom and not nom and normalize_text(agent.prenom) == prenom)
            ):
                results.append(agent)

        # Si trouvé dans le cache → retour immédiat
        if results:
            self.cache_manager.register_hit("Agent")
            return results

        # --- Sinon, on cherche dans les fichiers JSON ---
        all_data = self.list_all()
        for data in all_data:
            agent_nom = normalize_text(data.nom)
            agent_prenom = normalize_text(data.prenom)
            if (
                (nom and prenom and agent_nom == nom and agent_prenom == prenom)
                or (nom and not prenom and agent_nom == nom)
                or (prenom and not nom and agent_prenom == prenom)
            ):
                self._cache_set(str(data.id), data)
                results.append(data)

        if results:
            self.cache_manager.register_miss("Agent")
        return results