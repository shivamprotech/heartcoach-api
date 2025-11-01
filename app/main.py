from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import SQLModel
from app.core.config import settings
from app.routers.api_v1 import auth
from app.routers.api_v1 import health
from app.routers.api_v1 import user
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Runs once at startup
    print("🚀 Initializing database...")
    SQLModel.metadata.create_all(engine)
    yield
    # ✅ Runs once at shutdown
    print("🛑 Shutting down application...")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(user.router, prefix="/api/v1")
    return app


app = create_app()
