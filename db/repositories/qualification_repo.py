from models.qualification import Qualification

from db.base_repository import BaseRepository

class QualificationRepository(BaseRepository[Qualification]):
    def __init__(self, db):
        super().__init__(db, "qualifications", Qualification)

    def _serialize(self, obj: Qualification) -> dict:
        return obj.to_dict()

    def _deserialize(self, data: dict) -> Qualification:
        return Qualification.from_dict(data)

    def list_for_agent(self, agent_id: int) -> list[Qualification]:
        if not self._cache:
            self.list_all()
        return [q for q in self._cache.values() if q.agent_id == agent_id]

    def list_for_poste(self, poste_id: int) -> list[Qualification]:
        if not self._cache:
            self.list_all()
        return [q for q in self._cache.values() if q.poste_id == poste_id]
