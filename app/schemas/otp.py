from pydantic import BaseModel, EmailStr
from typing import Optional


class RequestOTPCreate(BaseModel):
    contact: str  # can be email or phone


class VerifyOTPPayload(BaseModel):
    contact: str
    otp: str
    device_info: Optional[str] = None


class ResendOtpPayload(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
