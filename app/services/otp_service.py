# app/services/otp_service.py
import secrets
import string
import time
from typing import Optional

from app.core.config import settings
from app.services.senders.email_sender import EmailSender  # new/updated sender below
from app.services.senders.phone_sender import PhoneSender
from redis.asyncio import Redis  # uses redis-py v4+ asyncio support

OTP_LENGTH = 6
OTP_EXPIRES_SECONDS = 3000  # 5 minutes
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

    def _generate_otp(self) -> str:
        # Use `secrets` for cryptographic randomness
        return "".join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))

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

    async def generate_and_send(self, contact: str) -> bool:
        """
        Generate OTP, store in Redis (or memory), and send via appropriate channel.
        Returns True if send attempt was initiated successfully.
        """
        otp = self._generate_otp()
        await self.store_otp(contact, otp)

        body = f"Your OTP is {otp}. It will expire in {OTP_EXPIRES_SECONDS // 60} minutes."

        # If email, call email sender. The email_sender.send_email is async.
        if "@" in contact:
            subject = "Your HeartCoach Verification Code"
            # send_email might be synchronous under the hood; EmailSender handles async wrapping.
            sent = await self.email_sender.send_email(to_email=contact, subject=subject, body=body)
            return bool(sent)
        else:
            sent = await self.phone_sender.send_phone(to_phone=contact, body=body)

        # TODO: if contact is phone, call sms/whatsapp senders and return their status
        # For now, return True (we generated and stored OTP)
        return True

    async def verify(self, contact: str, otp: str) -> bool:
        stored = await self.get_otp(contact)
        if not stored:
            return False
        if secrets.compare_digest(stored, otp):
            await self.delete_otp(contact)
            return True
        return False
