from typing import List
from datetime import date

from models.affectation import Affectation

from db.base_repository import BaseRepository

class AffectationRepository(BaseRepository[Affectation]):
    def __init__(self, db):
        super().__init__(db, "affectations", Affectation)

    def _serialize(self, obj: Affectation) -> dict:
        return obj.to_dict()

    def _deserialize(self, data: dict) -> Affectation:
        date_affectation = date.fromisoformat(data["jour"])

        return Affectation(
            agent_id=data["agent_id"],
            tranche_id=data["tranche_id"],
            jour=date_affectation
        )

    def list_for_agent(self, agent_id: int):
        if not self._cache:
            self.list_all()
        return [a for a in self._cache.values() if a.agent_id == agent_id]

    def list_for_tranche(self, tranche_id: int):
        if not self._cache:
            self.list_all()
        return [a for a in self._cache.values() if a.tranche_id == tranche_id]

    def list_in_period(self, start: date, end: date):
        if not self._cache:
            self.list_all()
        return [a for a in self._cache.values() if start <= a.jour <= end]
    
    def list_for_agent_and_period(
        self,
        agent_id: int,
        start_date: date,
        end_date: date
    ) -> List[Affectation]:
        """
        Retourne toutes les affectations d'un agent entre deux dates incluses.
        Utilise le cache si possible.
        """
        if not self._cache:
            self.list_all()

        return [
            a for a in self._cache.values()
            if a.agent_id == agent_id and start_date <= a.jour <= end_date
        ]