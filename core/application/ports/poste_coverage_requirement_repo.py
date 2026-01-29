from __future__ import annotations
from typing import List, Optional, Protocol, runtime_checkable

from core.domain.entities import PosteCoverageRequirement 

@runtime_checkable
class PosteCoverageRequirementRepositoryPort(Protocol):
    def list_for_poste(self, poste_id: int) -> List[PosteCoverageRequirement]: ...
    def replace_for_poste(self, poste_id: int, reqs: List[PosteCoverageRequirement]) -> None: ...