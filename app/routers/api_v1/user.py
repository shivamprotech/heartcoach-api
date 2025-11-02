# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_info_repo import UserInfoRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserInfoCreate, UserInfoResponse, UserResponse
from app.services.user_service import UserInfoService


router = APIRouter(prefix="/user", tags=["user"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserInfoService:
    repo = UserInfoRepository(db)
    return UserInfoService(repo)



@router.get("/me", response_model=UserResponse)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    """Return current user info using JWT token"""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user_repo = UserRepository(db)
    user = await user_repo.get_user_with_info(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.post("/{user_id}/create-profile", response_model=UserInfoResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(request: Request, user_info: UserInfoCreate,
                         user_svc: UserInfoService = Depends(get_user_service)):
    """ 
    pass
    """
    try:
        user_id = getattr(request.state, "user_id", None)
        user_info = await user_svc.get_or_create_user_info(user_id=user_id, user_info=user_info)
        return user_info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating/updating profile: {str(e)}"
        )
