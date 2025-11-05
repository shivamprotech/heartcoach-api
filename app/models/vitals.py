from sqlalchemy import Column, Float, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.db.base_class import Base  # Assuming you have a Base from SQLAlchemy setup


class ReadingTime(str, enum.Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    night = "night"


class UserVital(Base):
    __tablename__ = "user_vitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Optional health metrics
    systolic_bp = Column(Float, nullable=True)      # e.g., 120
    diastolic_bp = Column(Float, nullable=True)     # e.g., 80
    heart_rate = Column(Float, nullable=True)       # e.g., 72
    spo2 = Column(Float, nullable=True)             # e.g., 98
    weight = Column(Float, nullable=True)           # e.g., 70.5 (kg)

    # Reading context
    reading_time = Column(Enum(ReadingTime), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="vitals")
