# app/schemas/user.py
from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str]


class UserRead(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    full_name: Optional[str]
    is_active: Optional[bool]
