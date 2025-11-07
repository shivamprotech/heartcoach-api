from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.logging import setup_logger
from app.models.user import UserInfo
from app.schemas.user import UserInfoCreate

logger = setup_logger()


class UserInfoRepository:
    """Repository layer for performing CRUD operations on UserInfo."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> UserInfo | None:
        """
        Retrieve a user's profile information by their user ID.

        :param user_id: The unique identifier of the user.
        :type user_id: int
        :return: The user's profile if found, else None.
        :rtype: UserInfo | None
        """
        logger.info(f"Fetching UserInfo for user_id={user_id}")
        try:
            query = select(UserInfo).where(UserInfo.user_id == user_id)
            result = await self.db.execute(query)
            user_info = result.scalars().first()
            if user_info:
                logger.info(f"UserInfo found for user_id={user_id}")
            else:
                logger.warning(f"No UserInfo found for user_id={user_id}")
            return user_info
        except Exception as e:
            logger.error(f"Error fetching UserInfo for user_id={user_id}: {str(e)}")
            raise

    async def create_user_info(self, user_id: int, user_info: UserInfoCreate) -> UserInfo:
        """
        Create a new user profile record in the database.

        :param user_id: The ID of the user to link the profile with.
        :type user_id: int
        :param user_info: The user information payload.
        :type user_info: UserInfoCreate
        :return: The newly created UserInfo object.
        :rtype: UserInfo
        :raises Exception: If database commit fails.
        """
        logger.info(f"Creating new UserInfo for user_id={user_id}")
        try:
            data = user_info.model_dump(exclude_unset=True)
            info = UserInfo(user_id=user_id, **data)

            self.db.add(info)
            await self.db.commit()
            await self.db.refresh(info)

            logger.info(f"Successfully created UserInfo for user_id={user_id}")
            return info

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create UserInfo for user_id={user_id}: {str(e)}")
            raise

    async def update_user_info(self, user_id: int, user_info: UserInfoCreate) -> UserInfo:
        """
        Update an existing user's profile information.

        :param user_id: The unique ID of the user whose profile should be updated.
        :type user_id: int
        :param user_info: The new user information to update.
        :type user_info: UserInfoCreate
        :return: The updated UserInfo record.
        :rtype: UserInfo
        :raises Exception: If update or commit fails.
        """
        logger.info(f"Updating UserInfo for user_id={user_id}")
        try:
            data = user_info.model_dump(exclude_unset=True)

            query = (
                update(UserInfo)
                .where(UserInfo.user_id == user_id)
                .values(**data)
                .returning(UserInfo)
            )
            result = await self.db.execute(query)
            await self.db.commit()

            updated_info = result.scalars().first()
            logger.info(f"Successfully updated UserInfo for user_id={user_id}")
            return updated_info

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update UserInfo for user_id={user_id}: {str(e)}")
            raise
