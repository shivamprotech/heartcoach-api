# app/repositories/user_repo.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from typing import Optional


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        q = select(User).where(User.email == email)
        result = await self.session.execute(q)
        return result.scalars().first()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get(self, user_id: int) -> Optional[User]:
        q = select(User).where(User.id == user_id)
        result = await self.session.execute(q)
        return result.scalars().first()
