# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_info_repo import UserInfoRepository
from app.schemas.user import UserInfoCreate, UserInfoResponse
from app.services.user_service import UserInfoService


router = APIRouter(prefix="/user", tags=["user"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserInfoService:
    repo = UserInfoRepository(db)
    return UserInfoService(repo)


@router.post("/{user_id}/create-profile", response_model=UserInfoResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(user_id: str,
                         user_info: UserInfoCreate,
                         user_svc: UserInfoService = Depends(get_user_service)):
    """ 
    pass
    """
    try:
        user_info = await user_svc.get_or_create_user_info(user_id=user_id, user_info=user_info)
        return user_info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating/updating profile: {str(e)}"
        )
