from datetime import date
from typing import List
from models.etat_jour_agent import EtatJourAgent
from db.base_repository import BaseRepository


class EtatJourAgentRepository(BaseRepository[EtatJourAgent]):
    def __init__(self, db):
        super().__init__(db, "etat_jour_agents", EtatJourAgent)

    def _serialize(self, obj: EtatJourAgent) -> dict:
        return obj.to_dict()

    def _deserialize(self, data: dict) -> EtatJourAgent:
        return EtatJourAgent.from_dict(data)

    def get_for_agent_and_day(self, agent_id: int, jour: date) -> EtatJourAgent | None:
        """
        Récupère l'état d'un agent pour une journée donnée.
        """
        key = f"{agent_id}_{jour.strftime('%Y%m%d')}"
        return self.get(key)

    def list_for_agent(self, agent_id: int):
        """
        Liste tous les états journaliers d'un agent.
        """
        if not self._cache:
            self.list_all()
        return [e for e in self._cache.values() if e.agent_id == agent_id]
    
    def list_for_agent_by_type(self, agent_id: int, *types_jour: str) -> List[EtatJourAgent]:
        """
        Retourne tous les états journaliers correspondant à un ou plusieurs types.
        Ex : repo.list_for_agent_by_type(5, "ZCOT", "ABSENCE")
        """
        return [
            e for e in self.list_for_agent(agent_id)
            if e.type_jour in types_jour
        ]

    # ---------- Alias pratiques ----------

    def list_zcot_for_agent(self, agent_id: int) -> List[EtatJourAgent]:
        return self.list_for_agent_by_type(agent_id, "zcot")

    def list_absences_for_agent(self, agent_id: int) -> List[EtatJourAgent]:
        return self.list_for_agent_by_type(agent_id, "absence")

    def list_conges_for_agent(self, agent_id: int) -> List[EtatJourAgent]:
        return self.list_for_agent_by_type(agent_id, "conge")

    def list_repos_for_agent(self, agent_id: int) -> List[EtatJourAgent]:
        return self.list_for_agent_by_type(agent_id, "repos")

    def list_travail_for_agent(self, agent_id: int) -> List[EtatJourAgent]:
        return self.list_for_agent_by_type(agent_id, "poste")
