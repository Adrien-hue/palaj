from fastapi import FastAPI

from backend.app.settings import settings
from backend.app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    # /api/v1/...
    app.include_router(
        api_router,
        prefix=f"{settings.api_prefix}{settings.api_v1_prefix}",
    )
    return app


app = create_app()
