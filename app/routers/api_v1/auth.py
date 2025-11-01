# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.services.otp_service import OTPService
from app.services.auth_service import AuthService
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class RequestOTPIn(BaseModel):
    contact: str


class VerifyOTPIn(BaseModel):
    contact: str
    otp: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


async def get_otp_service() -> OTPService:
    # could accept injected redis client in future
    return OTPService()


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    repo = UserRepository(db)
    return AuthService(repo)


@router.post("/request-otp")
async def request_otp(payload: RequestOTPIn, otp_service: OTPService = Depends(get_otp_service)):
    """
    Generate and send OTP to contact (email or phone).
    """
    ok = await otp_service.generate_and_send(payload.contact)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    return {"message": f"OTP sent to {payload.contact}"}


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    payload: VerifyOTPIn,
    db: AsyncSession = Depends(get_db),
    otp_service: OTPService = Depends(get_otp_service),
    auth_svc: AuthService = Depends(get_auth_service),
):
    """
    Verify OTP; if valid, get_or_create the user and return a JWT access token.
    """
    valid = await otp_service.verify(payload.contact, payload.otp)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")

    # Create or fetch user (repo handles email vs phone)
    user_repo = auth_svc.user_repo  # AuthService constructed around repo
    user, created = await user_repo.get_or_create_by_contact(payload.contact)

    # Optionally: on user creation set defaults (e.g., is_active True) — repo.create handles that

    # Issue JWT token using AuthService
    token = auth_svc.create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
