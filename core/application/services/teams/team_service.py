from __future__ import annotations

from typing import List, Optional

from core.application.ports.team_repo import TeamRepositoryPort
from core.application.services.teams.exceptions import ConflictError, NotFoundError
from core.domain.entities.team import Team


class TeamService:
    def __init__(self, repo: TeamRepositoryPort):
        self.repo = repo

    def list_all(self) -> List[Team]:
        return self.repo.list_all()

    def get(self, team_id: int) -> Team:
        team = self.repo.get_by_id(team_id)
        if not team:
            raise NotFoundError(code="team_not_found", details={"team_id": team_id})
        return team

    def create(self, *, name: str, description: Optional[str]) -> Team:
        existing = self.repo.get_by_name(name)
        if existing:
            raise ConflictError(code="team_name_already_exists", details={"name": name})

        try:
            entity = Team(id=None, name=name, description=description, created_at=None)
            return self.repo.create(entity)
        except Exception:
            raise

    def update(self, team_id: int, *, name: Optional[str], description: Optional[str]) -> Team:
        current = self.repo.get_by_id(team_id)
        if not current:
            raise NotFoundError(code="team_not_found", details={"team_id": team_id})

        new_name = name if name is not None else current.name
        new_desc = description if description is not None else current.description

        # si le nom change : vérifier collision
        if new_name != current.name:
            existing = self.repo.get_by_name(new_name)
            if existing and existing.id != team_id:
                raise ConflictError(code="team_name_already_exists", details={"name": new_name})

        updated = Team(
            id=current.id,
            name=new_name,
            description=new_desc,
            created_at=current.created_at,
        )

        saved = self.repo.update(updated)
        if not saved:
            # très improbable (race condition delete), mais propre
            raise NotFoundError(code="team_not_found", details={"team_id": team_id})
        return saved

    def delete(self, team_id: int) -> None:
        # delete(id) retourne bool
        self.repo.delete(team_id)
