from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.auth import verify_api_key
from app.core.config import settings
from app.db.session import init_databases


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _on_startup() -> None:
        init_databases()

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    app.include_router(
        api_router,
        prefix="/api/v1",
        dependencies=[Depends(verify_api_key)],
    )
    return app


app = create_app()

