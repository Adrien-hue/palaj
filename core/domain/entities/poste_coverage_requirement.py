from dataclasses import dataclass

@dataclass(frozen=True)
class PosteCoverageRequirement:
    poste_id: int
    weekday: int
    tranche_id: int
    required_count: int = 1
