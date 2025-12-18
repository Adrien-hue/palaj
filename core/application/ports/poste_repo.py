from __future__ import annotations
from typing import List, Optional, Protocol, runtime_checkable
from core.domain.entities.poste import Poste


@runtime_checkable
class PosteRepositoryPort(Protocol):
    def get_by_id(self, poste_id: int) -> Optional[Poste]: ...
    def list_all(self) -> List[Poste]: ...
