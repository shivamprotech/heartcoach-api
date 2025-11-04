from pydantic import BaseModel, EmailStr
from typing import Optional


class RequestOTPIn(BaseModel):
    contact: str  # can be email or phone


class VerifyOTPIn(BaseModel):
    contact: str
    otp: str
    device_info: Optional[str] = None


class OTPResponse(BaseModel):
    message: str


class ResendOtpRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
