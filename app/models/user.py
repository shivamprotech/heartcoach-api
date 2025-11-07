import uuid
from enum import Enum
from sqlalchemy import Column, Date, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base
from sqlalchemy import Enum as SQLAlchemyEnum


class BloodGroupEnum(str, Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"


class UserRoleEnum(str, Enum):
    """Enumeration for different types of users in the system."""

    PATIENT = "Patient"
    DOCTOR = "Doctor"
    ADMIN = "Admin"
    GUEST = "Guest"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email: str = Column(String, unique=True, index=True)
    phone_number: str = Column(String, unique=True, index=True)

    # Relationship
    info = relationship("UserInfo", back_populates="user", uselist=False, cascade="all, delete-orphan")
    vitals = relationship("UserVital", back_populates="user", cascade="all, delete-orphan")
    medicines = relationship("Medicine", back_populates="user", cascade="all, delete-orphan")
    water_goals = relationship("WaterGoal", back_populates="user", cascade="all, delete-orphan")
    water_intake = relationship("WaterIntake", back_populates="user", cascade="all, delete-orphan")


class UserInfo(Base):
    """
    Represents detailed profile information for a user.
    Each user can have one UserInfo record containing personal and health-related details.
    """

    __tablename__ = "users_info"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(
        SQLAlchemyEnum(UserRoleEnum, name="user_role_enum"),
        nullable=False,
        default=UserRoleEnum.PATIENT
    )
    blood_group = Column(SQLAlchemyEnum(BloodGroupEnum, name="blood_group_enum"), nullable=True)

    # Updated: 'age' replaced with 'date_of_birth' for accuracy
    date_of_birth = Column(Date, nullable=True)

    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    # New: user profile image/avatar
    avatar_url = Column(String, nullable=True, comment="URL of the user's profile picture")

    is_active = Column(Boolean, default=True)

    # Relationship: One-to-one with User
    user = relationship("User", back_populates="info")
