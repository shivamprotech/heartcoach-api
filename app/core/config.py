import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "HeartCoach"
    ENV: str = "development"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    OPENAI_API_KEY: Optional[str] = None
    REDIS_URL: Optional[str] = None
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    PYTHONUNBUFFERED: int

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
