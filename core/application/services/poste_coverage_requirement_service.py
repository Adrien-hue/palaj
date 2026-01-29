from __future__ import annotations

from dataclasses import replace

from core.application.ports import (
    PosteCoverageRequirementRepositoryPort,
)
from core.domain.entities import PosteCoverageRequirement


class PosteCoverageRequirementService:
    def __init__(self, repo: PosteCoverageRequirementRepositoryPort):
        self.repo = repo

    def get_for_poste(self, poste_id: int) -> list[PosteCoverageRequirement]:
        return self.repo.list_for_poste(poste_id)

    def replace_for_poste(
        self,
        poste_id: int,
        reqs: list[PosteCoverageRequirement],
    ) -> list[PosteCoverageRequirement]:
        normalized = self._normalize_and_validate(poste_id, reqs)

        self.repo.replace_for_poste(poste_id, normalized)

        # Renvoi canonique (utile pour confirmer à l'API)
        return self.repo.list_for_poste(poste_id)

    # -----------------------
    # internals
    # -----------------------
    def _normalize_and_validate(
        self,
        poste_id: int,
        reqs: list[PosteCoverageRequirement],
    ) -> list[PosteCoverageRequirement]:
        # Normalisation + validations "métier"
        out: list[PosteCoverageRequirement] = []
        seen: set[tuple[int, int]] = set()  # (weekday, tranche_id)

        for r in reqs or []:
            # 1) weekday range (DB check existe aussi, mais on fail fast)
            if r.weekday < 0 or r.weekday > 6:
                raise ValueError(f"weekday must be in [0..6], got {r.weekday}")

            # 2) required_count
            if r.required_count is None:
                raise ValueError("required_count is required")
            if r.required_count < 0:
                raise ValueError(f"required_count must be >= 0, got {r.required_count}")

            # 3) tranche_id
            if r.tranche_id is None or r.tranche_id <= 0:
                raise ValueError(f"tranche_id must be a positive int, got {r.tranche_id}")

            # 4) doublons (évite un crash unique constraint + message plus clair)
            key = (r.weekday, r.tranche_id)
            if key in seen:
                raise ValueError(f"duplicate requirement for weekday={r.weekday} tranche_id={r.tranche_id}")
            seen.add(key)

            # 5) source de vérité: poste_id passé en param
            #    -> on écrase l'eventuel poste_id présent dans l'entité
            try:
                out.append(replace(r, poste_id=poste_id))
            except TypeError:
                # si ton entity n'est pas un dataclass, on reconstruit "à la main"
                out.append(
                    PosteCoverageRequirement(
                        poste_id=poste_id,
                        weekday=r.weekday,
                        tranche_id=r.tranche_id,
                        required_count=r.required_count,
                    )
                )

        return out
