# app/repositories/user_info_repo.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import UserInfo


class UserInfoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int):
        q = select(UserInfo).where(UserInfo.user_id == user_id)
        res = await self.db.execute(q)
        return res.scalars().first()

    async def create_user_info(self, user_id: int, user_info) -> UserInfo:
        data = user_info.model_dump(exclude_unset=True)
        info = UserInfo(user_id=user_id, **data)
        self.db.add(info)
        await self.db.commit()
        await self.db.refresh(info)
        return info

    async def update_user_info(self, user_id: int, user_info) -> UserInfo:
        data = user_info.model_dump(exclude_unset=True)
        q = (
            update(UserInfo)
            .where(UserInfo.user_id == user_id)
            .values(**data)
            .returning(UserInfo)
        )
        res = await self.db.execute(q)
        await self.db.commit()
        return res.scalars().first()
