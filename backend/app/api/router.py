from fastapi import APIRouter

from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.admin import router as admin_router
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.agent_teams import router as agent_teams_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.postes import router as postes_router
from backend.app.api.v1.qualifications import router as qualifications_router
from backend.app.api.v1.regimes import router as regimes_router
from backend.app.api.v1.teams import router as teams_router
from backend.app.api.v1.tranches import router as tranches_router
from backend.app.api.v1.rh import router as rh_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(admin_router)
api_router.include_router(agents_router)
api_router.include_router(agent_teams_router)
api_router.include_router(auth_router)
api_router.include_router(postes_router)
api_router.include_router(qualifications_router)
api_router.include_router(regimes_router)
api_router.include_router(teams_router)
api_router.include_router(tranches_router)
api_router.include_router(rh_router)