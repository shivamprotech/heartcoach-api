from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import date
from app.db.base_class import Base


class WaterGoal(Base):
    __tablename__ = "water_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal_ml = Column(Integer, nullable=False)
    created_at = Column(Date, default=date.today)

    user = relationship("User", back_populates="water_goals")


class WaterIntake(Base):
    __tablename__ = "water_intake"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    intake_ml = Column(Integer, nullable=False)
    date = Column(Date, default=date.today)

    user = relationship("User", back_populates="water_intake")
