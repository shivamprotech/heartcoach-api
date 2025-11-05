# app/schemas/medicine.py
from datetime import date, time, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class MedicineScheduleBase(BaseModel):
    time_of_day: time
    dose_label: Optional[str] = None
    dosage: Optional[str] = None


class MedicineScheduleCreate(MedicineScheduleBase):
    pass


class MedicineScheduleRead(MedicineScheduleBase):
    id: UUID

    class Config:
        orm_mode = True


class MedicineBase(BaseModel):
    name: str
    dosage: str
    notes: Optional[str] = None
    start_date: Optional[date] = Field(default_factory=date.today)
    end_date: Optional[date] = None


class MedicineCreate(MedicineBase):
    schedules: List[MedicineScheduleCreate]


class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    dosage: Optional[str] = None
    notes: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    schedules: Optional[List[MedicineScheduleCreate]] = None


class MedicineRead(MedicineBase):
    id: UUID
    schedules: List[MedicineScheduleRead] = []

    class Config:
        orm_mode = True


class MedicineHistoryRead(BaseModel):
    change_type: str
    old_value: Optional[str]
    new_value: Optional[str]
    changed_at: datetime

    class Config:
        orm_mode = True


class IntakeStatus(str, Enum):
    taken = "taken"
    missed = "missed"
    delayed = "delayed"


class MedicineIntakeCreate(BaseModel):
    status: IntakeStatus = Field(..., description="Intake status: taken/missed/delayed")
    schedule_id: Optional[str] = Field(None, description="Optional schedule reference (e.g., morning dose)")
    note: Optional[str] = Field(None, description="Optional note (e.g. 'Felt dizzy after')")


class MedicineIntakeRead(BaseModel):
    id: UUID
    medicine_id: str
    schedule_id: Optional[str]
    status: IntakeStatus
    note: Optional[str]
    taken_at: datetime
    recorded_at: datetime

    class Config:
        orm_mode = True
