from app.repositories.user_info_repo import UserInfoRepository


class UserInfoService:
    def __init__(self, user_info_repo: UserInfoRepository):
        self.user_info_repo = user_info_repo

    async def get_or_create_user_info(self, user_id: int, user_info):
        existing = await self.user_info_repo.get_by_user_id(user_id)
        if existing:
            return await self.user_info_repo.update_user_info(user_id, user_info)
        return await self.user_info_repo.create_user_info(user_id, user_info)
