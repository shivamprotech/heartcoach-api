import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "HeartCoach"
    ENV: str = "development"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 14400
    OPENAI_API_KEY: Optional[str] = None
    REDIS_URL: Optional[str] = None
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    PYTHONUNBUFFERED: int

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USER: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str

    PHONE_FROM: str = os.getenv("PHONE_FROM")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN")

    REDIS_URL: str | None = "redis://redis:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
