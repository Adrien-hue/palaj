from typing import Protocol

from core.domain.entities import AgentDay

class AgentDayAssignmentRepositoryPort(Protocol):
    def exists_for_tranche(self, tranche_id: int) -> bool: ...
