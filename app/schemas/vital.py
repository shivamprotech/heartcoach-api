from pydantic import BaseModel, Field
from typing import Annotated, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum


class ReadingTime(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    night = "night"


PositiveBP = Annotated[float, Field(gt=0, lt=300)]
PositiveWeight = Annotated[float, Field(gt=0, lt=500)]
PositiveHeartRate = Annotated[int, Field(gt=0, lt=250)]
PositiveSpO2 = Annotated[int, Field(gt=0, lt=100)]


class VitalBase(BaseModel):
    systolic_bp: Optional[PositiveBP] = None
    diastolic_bp: Optional[PositiveBP] = None
    heart_rate: Optional[PositiveHeartRate] = None
    spo2: Optional[PositiveSpO2] = None
    weight: Optional[PositiveWeight] = None


class VitalCreate(VitalBase):
    reading_time: ReadingTime = Field(..., description="Time of the day when vitals were recorded")


class VitalUpdate(VitalBase):
    reading_time: Optional[ReadingTime] = None


class VitalResponse(VitalCreate):
    id: UUID
    recorded_at: datetime

    class Config:
        orm_mode = True
