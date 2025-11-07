from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.core.logging import setup_logger
from app.models.user import User, UserInfo
from typing import Optional, Tuple
from app.schemas.user import UserCreate, UserInfoCreate
from sqlalchemy.orm import selectinload

logger = setup_logger()


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

    async def get_user_with_info(self, user_id: UUID):
        """
        Retrieve a user and their associated profile information from the database.

        This query performs a joined load (`selectinload`) on the related `info` model
        to avoid additional round trips when accessing user details.

        :param user_id: Unique identifier of the user to fetch
        :type user_id: str
        :return: The user instance with related info if found, else None
        :rtype: Optional[User]
        """
        logger.info(f"Fetching user with related info for user_id: {user_id}")

        try:
            # Build a query to fetch the user and pre-load related 'info' model
            query = (
                select(User)
                .options(selectinload(User.info))
                .where(User.id == user_id)
            )

            logger.debug(f"Executing user query for user_id: {user_id}")
            result = await self.session.execute(query)
            user = result.scalars().first()

            if not user:
                logger.warning(f"No user found for user_id: {user_id}")
                return None

            logger.debug(f"User fetched successfully for user_id: {user_id}")
            return user

        except Exception as e:
            logger.exception(f"Database error while fetching user {user_id}: {e}")
            raise

    async def create(self, user_in: UserCreate) -> User:
        """
        Create a new user from UserCreate input and return the saved user.

        :param user_in: Pydantic model with user data
        :type user_in: UserCreate
        :return: Created User instance
        :rtype: User
        """
        # Convert Pydantic model to ORM model
        user = User(**user_in.model_dump(exclude_unset=True))

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info(f"Created new user with id: {user.id}")
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
        Get an existing user by contact (email or phone), or create a new user if none exists.

        Steps:
        1. Determine if the contact is an email or phone number.
        2. Attempt to fetch the user by email or phone.
        3. If user exists, return it with created_flag=False.
        4. If user does not exist, create a new user and return it with created_flag=True.

        :param contact: Email or phone number of the user
        :type contact: str
        :return: Tuple of (User instance, created flag)
        :rtype: Tuple[User, bool]
        """
        logger.info(f"Fetching or creating user for contact: {contact}")

        # Step 1: Check if contact is email or phone
        if "@" in contact:
            # Attempt to fetch existing user by email
            existing = await self.get_by_email(contact)
            if existing:
                logger.info(f"Existing user found by email: {contact}, id: {existing.id}")
                return existing, False

            # Prepare user creation input for email
            user = UserCreate(email=contact)
            logger.info(f"No existing user found by email: {contact}. Preparing to create new user.")

        else:
            # Attempt to fetch existing user by phone
            existing = await self.get_by_phone(contact)
            if existing:
                logger.info(f"Existing user found by phone: {contact}, id: {existing.id}")
                return existing, False

            # Prepare user creation input for phone
            user = UserCreate(phone_number=contact)
            logger.info(f"No existing user found by phone: {contact}. Preparing to create new user.")

        # Step 2: Create new user
        user = await self.create(user)
        logger.info(f"New user created for contact: {contact}, id: {user.id}")

        return user, True

    async def update_avatar(self, user_id: UUID, avatar_url: str):
        """
        Update the user's avatar URL.
        """
        logger.info(f"Updating avatar for user {user_id}")

        stmt = (
            update(UserInfo)
            .where(UserInfo.user_id == user_id)
            .values(avatar_url=avatar_url)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(stmt)
        await self.session.commit()

        logger.info(f"Avatar URL updated for user {user_id}")
