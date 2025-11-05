from pydantic import BaseModel, Field


class WaterGoalCreate(BaseModel):
    goal_ml: int = Field(..., gt=0)


class WaterIntakeCreate(BaseModel):
    intake_ml: int = Field(..., gt=0)


class WaterStatus(BaseModel):
    goal_ml: int
    total_intake_ml: int
    remaining_ml: int
