from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

from app.models.user import BloodGroupEnum


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None


class UserInfoBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    role: Optional[str] = None


class UserCreate(UserBase):
    """Used when creating user after first OTP verification."""
    pass


class UserResponse(BaseModel):
    id: UUID
    email: Optional[str]
    phone_number: Optional[str]
    info: Optional[UserInfoBase]

    class Config:
        orm_mode = True


class UserInfoCreate(UserInfoBase):
    blood_group: BloodGroupEnum | None = None


class UserInfoResponse(UserInfoBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True
