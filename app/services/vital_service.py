from app.repositories.vital_repo import VitalRepository


class VitalService:
    def __init__(self):
        self.repo = VitalRepository()

    async def update_vital(self, db, user_id: int, vital_id: int, data: dict):
        vital = await self.repo.get_by_id(db, vital_id, user_id)
        if not vital:
            return None
        return await self.repo.update(db, vital, data)

    async def delete_vital(self, db, user_id: int, vital_id: int):
        vital = await self.repo.get_by_id(db, vital_id, user_id)
        if not vital:
            return None
        await self.repo.delete(db, vital)
        return True
