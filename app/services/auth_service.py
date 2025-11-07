from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.logging import setup_logger

logger = setup_logger()


class AuthService:
    def __init__(self):
        pass

    def create_access_token(self, subject: str, expires_delta: timedelta = None) -> str:
        """
        Create a JWT access token for a given subject (usually user ID).

        :param subject: Identifier for the token owner (e.g., user ID)
        :type subject: str
        :param expires_delta: Optional timedelta for token expiration
        :type expires_delta: timedelta, optional
        :return: Encoded JWT token string
        :rtype: str
        """
        try:
            # Determine expiration time
            expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
            payload = {
                "exp": expire,
                "sub": str(subject)
            }

            # Log token creation
            logger.info(f"Creating JWT access token for subject: {subject}, expires at {expire.isoformat()}")

            # Encode JWT token
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
            return token

        except Exception as e:
            logger.exception(f"Failed to create access token for subject: {subject}: {e}")
            raise
