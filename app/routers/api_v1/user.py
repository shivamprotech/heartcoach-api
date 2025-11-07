# app/routes/auth.py
import os
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.core.deps import get_user_id, get_user_repo, get_user_service
from app.core.logging import setup_logger
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserInfoCreate, UserInfoResponse, UserResponse
from app.services.user_service import UserInfoService

router = APIRouter(prefix="/user", tags=["user"])
logger = setup_logger()


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_repo: UserRepository = Depends(get_user_repo),
    user_id: UUID = Depends(get_user_id),
):
    """
    Retrieve the currently authenticated user's profile information.

    This endpoint uses the user ID extracted from the JWT token to fetch
    detailed user information from the database. It ensures the user exists
    before returning their data.

    :param user_repo: Repository layer responsible for accessing user data.
    :type user_repo: UserRepository
    :param user_id: The authenticated user's unique UUID, extracted from JWT.
    :type user_id: UUID
    :raises HTTPException: 404 error if the user is not found in the database.
    :return: The authenticated user's profile details.
    :rtype: UserResponse
    """
    logger.info(f"Fetching profile details for user_id: {user_id}")

    try:
        user = await user_repo.get_user_with_info(user_id)

        if not user:
            logger.warning(f"User not found in database for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        logger.debug(f"Successfully retrieved profile for user_id: {user_id}")
        return user

    except HTTPException:
        # Already logged — re-raise as-is
        raise
    except Exception as e:
        logger.exception(f"Unexpected error fetching user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching user info"
        )


@router.post("/upload-avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: UUID = Depends(get_user_id),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """
    Upload a user's avatar image and update their profile.

    This endpoint allows an authenticated user to upload a profile picture.
    The file is saved locally under the `/static/uploads/` directory and 
    the user's record is updated with the corresponding avatar URL.

    :param file: The uploaded image file.
    :type file: UploadFile
    :param user_id: The authenticated user's unique identifier, extracted from JWT.
    :type user_id: UUID
    :param user_repo: Repository layer responsible for accessing user data.
    :type user_repo: UserRepository
    :raises HTTPException:
        - 500: If the file upload or database update fails.
    :return: A JSON object containing the avatar URL.
    :rtype: dict
    """
    logger.info(f"[upload_avatar] User {user_id} started avatar upload: {file.filename}")

    try:
        # Ensure upload directory exists
        uploads_dir = "static/uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        logger.debug(f"[upload_avatar] Upload directory verified: {uploads_dir}")

        # Save the uploaded file locally
        filename = f"{user_id}_{file.filename}"
        file_path = os.path.join(uploads_dir, filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        avatar_url = f"/static/uploads/{filename}"
        logger.debug(f"[upload_avatar] File saved successfully at: {file_path}")

        # Update user avatar in database
        await user_repo.update_avatar(user_id, avatar_url)

        logger.info(f"[upload_avatar] Avatar successfully updated for user {user_id}: {avatar_url}")
        return {"avatar_url": avatar_url}

    except Exception as e:
        logger.exception(f"[upload_avatar] Failed to upload avatar for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")


@router.post(
    "/{user_id}/upsert-profile",
    response_model=UserInfoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_profile(
    user_info: UserInfoCreate,
    user_id: UUID = Depends(get_user_id),
    user_svc: UserInfoService = Depends(get_user_service),
):
    """
    Create or update the authenticated user's profile information.

    This endpoint either creates a new user profile or updates the 
    existing one for the authenticated user. It accepts structured
    user information such as name, date of birth, blood group, etc.

    :param user_info: The user's profile data payload.
    :type user_info: UserInfoCreate
    :param user_id: The authenticated user's unique identifier.
    :type user_id: UUID
    :param user_svc: Service layer responsible for managing user info.
    :type user_svc: UserInfoService
    :raises HTTPException:
        - 500: If the profile creation or update fails.
    :return: The created or updated user profile.
    :rtype: UserInfoResponse
    """
    logger.info(f"[create_profile] User {user_id} requested profile creation/update")

    try:
        user_info = await user_svc.get_or_create_user_info(user_id=user_id, user_info=user_info)
        logger.info(f"[create_profile] Profile successfully created/updated for user {user_id}")
        return user_info

    except Exception as e:
        logger.exception(f"[create_profile] Error creating/updating profile for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating/updating profile: {str(e)}")
