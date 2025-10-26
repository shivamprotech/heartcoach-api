from fastapi import FastAPI
from app.core.config import settings
from app.routers.api_v1 import auth
from app.routers.api_v1 import health


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    return app


app = create_app()
