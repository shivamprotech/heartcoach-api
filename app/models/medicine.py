from sqlalchemy import Column, DateTime, String, Date, Text, Time, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import date, datetime
import enum, uuid

from app.db.base_class import Base


class MedicineStatus(str, enum.Enum):
    PENDING = "pending"
    TAKEN = "taken"
    MISSED = "missed"


class IntakeStatus(str, enum.Enum):
    TAKEN = "taken"
    MISSED = "missed"
    DELAYED = "delayed"


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)  # e.g. "2mg"
    notes = Column(String, nullable=True)

    start_date = Column(Date, default=date.today)
    end_date = Column(Date, nullable=True)

    schedules = relationship("MedicineSchedule", back_populates="medicine", cascade="all, delete-orphan")
    history = relationship("MedicineHistory", back_populates="medicine", cascade="all, delete")
    user = relationship("User", back_populates="medicines")


class MedicineSchedule(Base):
    __tablename__ = "medicine_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    time_of_day = Column(Time, nullable=False)       # e.g. 07:00, 16:00, 21:00
    dose_label = Column(String, nullable=True)       # e.g. "Morning", "Afternoon", "Night"
    dosage = Column(String, nullable=True)

    medicine = relationship("Medicine", back_populates="schedules")


class MedicineHistory(Base):
    __tablename__ = "medicine_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    change_type = Column(String, nullable=False)        # e.g. "update_dosage", "time_changed"
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

    medicine = relationship("Medicine", back_populates="history")


class MedicineIntakeHistory(Base):
    __tablename__ = "medicine_intake_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    schedule_id = Column(UUID(as_uuid=True), ForeignKey("medicine_schedules.id", ondelete="CASCADE"), nullable=True)

    status = Column(Enum(IntakeStatus), nullable=False)
    note = Column(Text, nullable=True)
    taken_at = Column(DateTime, default=datetime.utcnow)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    medicine = relationship("Medicine")
    schedule = relationship("MedicineSchedule")
