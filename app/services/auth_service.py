# app/services/auth_service.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.repositories.user_repo import UserRepository
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def verify_password(self, plain, hashed):
        return pwd_context.verify(plain, hashed)

    def hash_password(self, pw: str) -> str:
        return pwd_context.hash(pw)

    def create_access_token(self, subject: str, expires_delta: timedelta = None):
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode = {"exp": expire, "sub": str(subject)}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

    async def authenticate(self, email: str, password: str) -> User | None:
        user = await self.user_repo.get_by_email(email)
        if user and self.verify_password(password, user.hashed_password):
            return user
        return None
