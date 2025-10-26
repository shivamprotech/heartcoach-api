# app/routers/api_v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.db.session import get_db
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


async def get_auth_service(db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return AuthService(repo)


@router.post("/signup", response_model=UserRead)
async def signup(payload: UserCreate, auth_svc: AuthService = Depends(get_auth_service)):
    existing = await auth_svc.user_repo.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email exists")
    hashed = auth_svc.hash_password(payload.password)
    user = User(email=payload.email, hashed_password=hashed, full_name=payload.full_name)
    created = await auth_svc.user_repo.create(user)
    return created


@router.post("/token")
async def login_for_token(form_data: dict, auth_svc: AuthService = Depends(get_auth_service)):
    # in production, use OAuth2PasswordRequestForm
    user = await auth_svc.authenticate(form_data["username"], form_data["password"])
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth_svc.create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer"}
