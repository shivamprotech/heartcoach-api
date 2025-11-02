# app/repositories/user_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserInfo
from typing import Optional, Tuple
from app.schemas.user import UserCreate, UserInfoCreate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        q = select(User).where(User.email == email)
        result = await self.session.execute(q)
        return result.scalars().first()

    async def get_by_phone(self, phone: str) -> Optional[User]:
        q = select(User).where(User.phone_number == phone)
        result = await self.session.execute(q)
        return result.scalars().first()

    async def create(self, user_in: UserCreate) -> User:
        # Convert Pydantic → ORM
        user_data = user_in.model_dump(exclude_unset=True)
        user = User(**user_data)

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def create_user_info(self, user_id: int, user_info: UserInfoCreate) -> UserInfo:
        if hasattr(user_info, "model_dump"):
            user_info_data = user_info.model_dump(exclude_unset=True)
        else:
            user_info_data = user_info.dict(exclude_unset=True)
        info = UserInfo(user_id=user_id, **user_info_data)
        self.db.add(info)
        await self.db.commit()
        await self.db.refresh(info)
        return info

    async def get(self, user_id: int) -> Optional[User]:
        q = select(User).where(User.id == user_id)
        result = await self.session.execute(q)
        return result.scalars().first()

    async def get_or_create_by_contact(self, contact: str) -> Tuple[User, bool]:
        """
        If contact looks like an email, fetch/create by email; else by phone.
        Returns (user, created_flag)
        """
        if "@" in contact:
            existing = await self.get_by_email(contact)
            if existing:
                return existing, False
            user_in = UserCreate(email=contact)
        else:
            existing = await self.get_by_phone(contact)
            if existing:
                return existing, False
            user_in = UserCreate(phone_number=contact)

        user = await self.create(user_in)
        return user, True
