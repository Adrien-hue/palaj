from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.settings import settings
from backend.app.dto._rebuild import rebuild_dtos
from backend.app.api.router import api_router


def create_app() -> FastAPI:
    rebuild_dtos()

    app = FastAPI(title=settings.app_name, debug=settings.debug)

    origins = settings.cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # /api/v1/...
    app.include_router(
        api_router,
        prefix=f"{settings.api_prefix}{settings.api_v1_prefix}",
    )

    return app


app = create_app()
