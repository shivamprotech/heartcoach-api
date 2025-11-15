from sqlalchemy import Column, DateTime, Index, String, Date, Text, Time, ForeignKey, Enum, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import date, datetime
import enum, uuid

from app.db.base_class import Base
from app.db.mixins import AsyncVersionedMixin
from app.models.common import TimestampMixin


class IntakeStatus(str, enum.Enum):
    PENDING = "pending"   # New day, scheduled dose not yet taken
    TAKEN = "taken"       # User confirmed the dose
    MISSED = "missed"     # Automatically or manually marked missed
    DELAYED = "delayed"   # User snoozed or indicated a late intake


class Medicine(Base, TimestampMixin, AsyncVersionedMixin):
    __tablename__ = "medicines"
    __versioned__ = {}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    notes = Column(String, nullable=True)

    start_date = Column(Date, default=date.today)
    end_date = Column(Date, nullable=True)

    schedules = relationship("MedicineSchedule", back_populates="medicine", cascade="all, delete-orphan")
    user = relationship("User", back_populates="medicines")


class MedicineSchedule(Base, TimestampMixin):
    __tablename__ = "medicine_schedules"
    __versioned__ = {}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicine_id = Column(UUID(as_uuid=True), ForeignKey("medicines.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    time_of_day = Column(Time, nullable=False)       # e.g. 07:00, 16:00, 21:00
    dose_label = Column(String, nullable=True)       # e.g. "Morning", "Afternoon", "Night"
    dosage = Column(String, nullable=True)

    medicine = relationship("Medicine", back_populates="schedules")
    daily_intakes = relationship(
        "DailyMedicineIntake",
        back_populates="schedule",
        cascade="all, delete-orphan",
    )


class DailyMedicineIntake(Base, TimestampMixin):
    __tablename__ = "daily_medicine_intakes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # One row per schedule per day
    schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey("medicine_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )

    # The local date this dose applies to (user’s timezone)
    intake_date = Column(Date, nullable=False, default=date.today)

    # Current status for this schedule & date
    status = Column(
        Enum(IntakeStatus, name="intake_status"),
        nullable=False,
        default=IntakeStatus.PENDING,
    )

    # When the status was last changed (TAKEN / MISSED / DELAYED, etc.)
    status_changed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Snapshot of scheduled time-of-day for easier querying / analytics
    scheduled_time = Column(Time, nullable=False)

    # Optional note for that day’s intake (“felt nauseous”, “took late”, etc.)
    note = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="daily_intakes", lazy="joined")
    schedule = relationship("MedicineSchedule", back_populates="daily_intakes")

    __table_args__ = (
        # One row per (schedule, date)
        UniqueConstraint(
            "schedule_id",
            "intake_date",
            name="uq_daily_intake_schedule_date",
        ),
        # Fast lookups by user + date
        Index(
            "ix_daily_intake_user_date",
            "user_id",
            "intake_date",
        ),
    )
