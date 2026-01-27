from __future__ import annotations

from typing import Any, List, Optional

from core.application.ports.team_repo import TeamRepositoryPort
from core.application.services.teams.exceptions import ConflictError, NotFoundError
from core.domain.entities.team import Team


class TeamService:
    def __init__(self, repo: TeamRepositoryPort):
        self.repo = repo

    def count(self) -> int:
        return self.repo.count()

    def list(self, *, limit: Optional[int] = None, offset: int = 0) -> List[Team]:
        return self.repo.list(limit=limit, offset=offset)

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

    def update(self, team_id: int, **changes: Any) -> Team:
        current = self.repo.get_by_id(team_id)
        if not current:
            raise NotFoundError(code="team_not_found", details={"team_id": team_id})

        # --- NAME ---
        if "name" in changes:
            raw_name = changes["name"]
            if raw_name is None or str(raw_name).strip() == "":
                raise ValueError("Team.name cannot be null/empty")  # ou ValidationError maison

            new_name = str(raw_name).strip()

            if new_name != current.name:
                existing = self.repo.get_by_name(new_name)
                if existing and existing.id != team_id:
                    raise ConflictError(
                        code="team_name_already_exists",
                        details={"name": new_name},
                    )
        else:
            new_name = current.name

        # --- DESCRIPTION ---
        if "description" in changes:
            raw_desc = changes["description"]

            if raw_desc is None:
                # clear explicite
                new_desc = None
            else:
                desc = str(raw_desc).strip()
                new_desc = None if desc == "" else desc
        else:
            new_desc = current.description

        updated = Team(
            id=current.id,
            name=new_name,
            description=new_desc,
            created_at=current.created_at,
        )

        saved = self.repo.update(updated)
        if not saved:
            raise NotFoundError(code="team_not_found", details={"team_id": team_id})

        return saved

    def delete(self, team_id: int) -> None:
        # delete(id) retourne bool
        self.repo.delete(team_id)
