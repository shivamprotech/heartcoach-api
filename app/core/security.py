import hashlib, hmac, secrets, uuid
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings


def gen_numeric_otp(length=6):
    return str(secrets.randbelow(10**length)).zfill(length)


def hash_otp(contact: str, otp: str):
    msg = f"{contact}|{otp}".encode()
    return hmac.new(settings.OTP_SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()


def create_access_token(user_id: int):
    now = datetime.utcnow()
    exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": exp.timestamp(), "iat": now.timestamp()}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def create_refresh_token_jti():
    return str(uuid.uuid4())


def create_refresh_token_jwt(jti: str, user_id: int, expires_at: datetime):
    payload = {"sub": str(user_id), "jti": jti, "exp": expires_at.timestamp()}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
