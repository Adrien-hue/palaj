from datetime import datetime
from typing import cast

from backend.app.dto.team import TeamDTO
from core.domain.entities.team import Team


def to_team_dto(t: Team) -> TeamDTO:
    if t.id is None:
        raise ValueError("Team.id is None: cannot map to TeamDTO (expected persisted entity).")

    if t.created_at is None:
        raise ValueError("Team.created_at is None: cannot map to TeamDTO (expected persisted entity).")

    return TeamDTO(
        id=int(t.id),
        name=t.name,
        description=t.description,
        created_at=cast(datetime, t.created_at),
    )
