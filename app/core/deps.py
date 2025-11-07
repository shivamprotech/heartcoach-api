

from fastapi import Depends, HTTPException, Request, status
from app.core.logging import setup_logger
from app.db.session import get_db
from app.repositories.user_info_repo import UserInfoRepository
from app.repositories.user_repo import UserRepository
from app.services.otp_service import OTPService
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserInfoService

logger = setup_logger()


async def get_otp_service() -> OTPService:
    return OTPService()


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserInfoService:
    repo = UserInfoRepository(db)
    return UserInfoService(repo)


async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency that returns a UserRepository instance.
    Can later accept injected DB session or other services.
    """
    return UserRepository(db)


async def get_user_id(request: Request):
    """
    Dependency to retrieve the currently authenticated user's ID from the request state.

    This assumes that authentication middleware has already validated the token
    and stored `user_id` in `request.state`.

    :param request: The incoming FastAPI request object.
    :type request: Request
    :raises HTTPException: If user_id is missing (unauthorized request).
    :return: The authenticated user's ID.
    :rtype: str or UUID
    """
    try:
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            logger.warning("Unauthorized request — missing user_id in request state.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized"
            )

        logger.debug(f"Authenticated request for user_id: {user_id}")
        return user_id

    except Exception as e:
        logger.exception(f"Error while retrieving user_id from request state: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while authenticating user"
        )
