from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True)
    phone_number: str = Column(String, unique=True, index=True)
    # Relationship to UserInfo
    info = relationship("UserInfo", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserInfo(Base):
    __tablename__ = "users_info"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    first_name: str | None = Column(String)
    last_name: str | None = Column(String)
    blood_group: str | None = Column(String)
    age: int | None = Column(Integer)
    height: float | None = Column(Float)
    weight: float | None = Column(Float)
    city: str | None = Column(String)
    country: str | None = Column(String)
    pincode: str | None = Column(String)
    is_active: bool = Column(Boolean, default=True)
    # Back-reference to User
    user = relationship("User", back_populates="info")