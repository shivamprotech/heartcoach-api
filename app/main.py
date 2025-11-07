from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError
from app.core.config import settings
from app.routers.api_v1 import auth, health, user, vital, medicine, water
from app.core.logging import setup_logger


def create_app() -> FastAPI:
    logger = setup_logger()

    # Lifespan context manager replaces on_event startup/shutdown
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        logger.info("HeartCoach API starting up...")
        yield
        # Shutdown
        logger.info("HeartCoach API shutting down...")

    app = FastAPI(title=settings.APP_NAME)

    # Create static directory if not exists
    os.makedirs("static/uploads", exist_ok=True)

    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        logger.info("HeartCoach API starting up...")

    # -----------------------------------------------------
    # 🧩 JWT Auth Middleware
    # -----------------------------------------------------
    @app.middleware("http")
    async def jwt_middleware(request: Request, call_next):
        """Global middleware to check JWT Bearer tokens."""
        # Public (unauthenticated) routes
        public_paths = [
            "/api/v1/auth/health",
            "/api/v1/auth/request-otp",
            "/api/v1/auth/verify-otp",
            "/api/v1/auth/resend-otp",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

        # Skip auth for public routes
        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        # Extract token
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return JSONResponse(
                status_code=401, content={"detail": "Missing or invalid Authorization header"}
            )

        try:
            # Decode JWT
            payload = jwt.decode(token.split(" ")[1], settings.SECRET_KEY, algorithms=["HS256"])
            # Store user_id in request.state for access in routes
            request.state.user_id = payload.get("sub")
        except JWTError:
            return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

        return await call_next(request)

    # -----------------------------------------------------
    # 🧩 OpenAPI Customization for Swagger Auth Support
    # -----------------------------------------------------
    def custom_openapi():
        """Add Bearer Auth scheme to Swagger UI."""
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=settings.APP_NAME,
            version="1.0.0",
            description="HeartCoach API with JWT Middleware Auth",
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
        openapi_schema["security"] = [{"bearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # -----------------------------------------------------
    # 🧩 Routers
    # -----------------------------------------------------
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(user.router, prefix="/api/v1")
    app.include_router(vital.router, prefix="/api/v1")
    app.include_router(medicine.router, prefix="/api/v1")
    app.include_router(water.router, prefix="/api/v1")

    return app


app = create_app()
