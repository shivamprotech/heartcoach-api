# app/services/otp_service.py
import secrets
import string
import time
import pyotp
from typing import Optional

from app.core.config import settings
from app.services.senders.email_sender import EmailSender  # new/updated sender below
from app.services.senders.phone_sender import PhoneSender
from redis.asyncio import Redis  # uses redis-py v4+ asyncio support

OTP_LENGTH = 6
OTP_EXPIRES_SECONDS = 18000  # 5 minutes
OTP_PREFIX = "heartcoach:otp:"


class OTPService:
    def __init__(self, redis_client: Optional[Redis] = None):
        # Prefer an injected redis client; create if settings present
        if redis_client is not None:
            self.redis = redis_client
        else:
            if settings.REDIS_URL:
                self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            else:
                self.redis = None  # use fallback store below

        # Sender abstraction (email; later add sms/whatsapp)
        self.email_sender = EmailSender()
        self.phone_sender = PhoneSender()

        # In-memory fallback (not across processes!)
        self._mem_store = {}

    def _otp_key(self, contact: str) -> str:
        return f"{OTP_PREFIX}{contact}"

    async def generate_otp(self, contact: str):
        # Create a unique secret per contact
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, interval=settings.OTP_VALIDITY_MINUTES * 60)
        otp = totp.now()

        # Store secret in Redis for later verification
        await self.redis.setex(f"otp_secret:{contact}", settings.OTP_VALIDITY_MINUTES * 60, secret)

        return otp

    async def store_otp(self, contact: str, otp: str) -> None:
        key = self._otp_key(contact)
        if self.redis:
            await self.redis.set(key, otp, ex=OTP_EXPIRES_SECONDS)
        else:
            # Fallback: store in-memory with expiry timestamp
            self._mem_store[contact] = (otp, time.time() + OTP_EXPIRES_SECONDS)

    async def get_otp(self, contact: str) -> Optional[str]:
        key = self._otp_key(contact)
        if self.redis:
            return await self.redis.get(key)
        else:
            data = self._mem_store.get(contact)
            if not data:
                return None
            otp, expires_at = data
            if time.time() > expires_at:
                self._mem_store.pop(contact, None)
                return None
            return otp

    async def delete_otp(self, contact: str) -> None:
        key = self._otp_key(contact)
        if self.redis:
            await self.redis.delete(key)
        else:
            self._mem_store.pop(contact, None)

    async def _generate_secret_and_otp(self, contact: str):
        """Generate new secret and OTP for a contact."""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret, interval=OTP_EXPIRES_SECONDS)
        otp = totp.now()
        await self.redis.setex(f"otp_secret:{contact}", OTP_EXPIRES_SECONDS, secret)
        return otp

    async def generate_and_send(self, contact: str) -> bool:
        """Generate new OTP and send."""
        otp = await self._generate_secret_and_otp(contact)
        return await self._send(contact, otp)

    async def fetch_and_send(self, contact: str) -> bool:
        """
        Fetch existing OTP if still valid, else generate a new one, then send it.
        """
        secret = await self.redis.get(f"otp_secret:{contact}")
        if secret:
            if isinstance(secret, bytes):
                secret = secret.decode()
            # Existing valid secret → regenerate same OTP
            totp = pyotp.TOTP(secret, interval=OTP_EXPIRES_SECONDS)
            otp = totp.now()
        else:
            # No secret → generate new one
            otp = await self._generate_secret_and_otp(contact)

        # Send the same (or new) OTP
        return await self._send(contact, otp, True)

    async def _send(self, contact: str, otp: str, resend: bool = False) -> bool:
        """Send OTP via appropriate channel."""
        if resend:
            body = f"Your OTP has been resend {otp}. It will expire in {OTP_EXPIRES_SECONDS // 60} minutes."
        else:
            body = f"Your OTP is {otp}. It will expire in {OTP_EXPIRES_SECONDS // 60} minutes."
        if "@" in contact:
            subject = "Your HeartCoach Verification Code"
            return await self.email_sender.send_email(to_email=contact, subject=subject, body=body)
        else:
            return await self.phone_sender.send_phone(to_phone=contact, body=body)

    async def verify(self, contact: str, otp: str) -> bool:
        """
        Verify a given OTP using the stored secret.
        """
        secret = await self.redis.get(f"otp_secret:{contact}")
        if not secret:
            return False

        if isinstance(secret, bytes):
            secret = secret.decode()

        totp = pyotp.TOTP(secret, interval=OTP_EXPIRES_SECONDS)
        return totp.verify(otp)
