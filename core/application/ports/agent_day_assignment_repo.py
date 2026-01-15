from typing import Protocol

class AgentDayAssignmentRepositoryPort(Protocol):
    def exists_for_tranche(self, tranche_id: int) -> bool: ...
