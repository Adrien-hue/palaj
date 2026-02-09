from fastapi import APIRouter, Depends

from backend.app.api.deps_authorization import require_role
from db.models import User

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/ping")
def admin_ping(_: User = Depends(require_role("admin"))):
    """
    Endpoint de test RBAC.
    Accessible uniquement aux utilisateurs avec le rôle 'admin'.
    """
    return {"status": "ok", "role_required": "admin"}
