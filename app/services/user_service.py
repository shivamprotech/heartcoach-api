from app.core.logging import setup_logger
from app.repositories.user_info_repo import UserInfoRepository

logger = setup_logger()


class UserInfoService:
    def __init__(self, user_info_repo: UserInfoRepository):
        self.user_info_repo = user_info_repo

    async def get_or_create_user_info(self, user_id: int, user_info):
        """
        Retrieve existing user profile or create a new one if none exists.

        This method checks whether a user info record exists for the given user ID.
        If it exists, the profile is updated with the new information.
        Otherwise, a new user info record is created and stored in the database.

        :param user_id: Unique identifier of the user.
        :type user_id: int
        :param user_info: Data containing profile fields to create or update.
        :type user_info: UserInfoCreate | dict
        :return: The created or updated user info record.
        :rtype: UserInfo
        """
        logger.info(f"[get_or_create_user_info] Checking existing profile for user {user_id}")

        try:
            # Fetch existing user info by user_id
            existing = await self.user_info_repo.get_by_user_id(user_id)

            if existing:
                logger.info(f"[get_or_create_user_info] Existing profile found for user {user_id}, updating record")
                # Update existing user info
                updated_info = await self.user_info_repo.update_user_info(user_id, user_info)
                logger.debug(f"[get_or_create_user_info] Profile successfully updated for user {user_id}")
                return updated_info

            # No record found → create new user info
            logger.info(f"[get_or_create_user_info] No profile found for user {user_id}, creating new record")
            new_info = await self.user_info_repo.create_user_info(user_id, user_info)
            logger.debug(f"[get_or_create_user_info] Profile successfully created for user {user_id}")
            return new_info

        except Exception as e:
            logger.exception(f"[get_or_create_user_info] Failed to create/update profile for user {user_id}: {e}")
            raise
