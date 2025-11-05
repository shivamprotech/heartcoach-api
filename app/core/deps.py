

from app.services.otp_service import OTPService


async def get_otp_service() -> OTPService:
    # could accept injected redis client in future
    return OTPService()
