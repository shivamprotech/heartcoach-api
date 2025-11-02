from uuid import UUID
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    """Used when creating user after first OTP verification."""
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None


class UserInfoBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    blood_group: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None

# class UserInfoResponse(BaseModel):
#     first_name: str = None
#     last_name: str = None
#     blood_group: str = None
#     age: int = None
#     height: float = None
#     weight: float = None
#     city: str = None
#     country: str = None
#     pincode: str = None
#     is_active: bool = True


class UserInfoCreate(UserInfoBase):
    pass


class UserInfoResponse(UserInfoBase):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
