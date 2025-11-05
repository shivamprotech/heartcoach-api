from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.vital import UserVital


class VitalRepository:
    async def get_by_id(self, db: AsyncSession, vital_id: int, user_id: int):
        result = await db.execute(select(UserVital).where(UserVital.id == vital_id, UserVital.user_id == user_id))
        return result.scalars().first()

    async def update(self, db: AsyncSession, vital: UserVital, data: dict):
        for key, value in data.items():
            setattr(vital, key, value)
        db.add(vital)
        await db.commit()
        await db.refresh(vital)
        return vital

    async def delete(self, db: AsyncSession, vital: UserVital):
        await db.delete(vital)
        await db.commit()
        return True
