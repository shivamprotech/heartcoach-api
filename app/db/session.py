from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# ✅ Use asyncpg in connection URL
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# ✅ Create async engine
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# ✅ Create async session
async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# ✅ Dependency for FastAPI routes
async def get_db():
    async with async_session() as session:
        yield session
