from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.session import get_db
from app.models.water import WaterGoal, WaterIntake
from app.schemas.water import WaterGoalCreate, WaterIntakeCreate, WaterStatus
from datetime import date

router = APIRouter(prefix="/water", tags=["Water"])


# Helper to get today's intake
async def get_today_intake(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(WaterIntake).where(WaterIntake.user_id == user_id, WaterIntake.date == date.today())
    )
    intake = result.scalar_one_or_none()
    return intake


# Set daily water goal
@router.post("/goal")
async def set_water_goal(request: Request, payload: WaterGoalCreate, db: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    goal = WaterGoal(user_id=user_id, goal_ml=payload.goal_ml)
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return {"message": "Goal set", "goal_ml": goal.goal_ml}


# Log water intake
@router.post("/intake")
async def log_water_intake(request: Request, payload: WaterIntakeCreate, db: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    intake = await get_today_intake(db, user_id)
    if intake:
        intake.intake_ml += payload.intake_ml
    else:
        intake = WaterIntake(user_id=user_id, intake_ml=payload.intake_ml)
        db.add(intake)

    await db.commit()
    await db.refresh(intake)
    return {"message": "Intake logged", "total_intake_ml": intake.intake_ml}


# Get progress/status
@router.get("/status", response_model=WaterStatus)
async def get_water_status(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # get latest goal
    result = await db.execute(
        select(WaterGoal).where(WaterGoal.user_id == user_id).order_by(WaterGoal.created_at.desc())
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Water goal not set")

    intake = await get_today_intake(db, user_id)
    total_intake = intake.intake_ml if intake else 0
    remaining = max(goal.goal_ml - total_intake, 0)

    return WaterStatus(
        goal_ml=goal.goal_ml,
        total_intake_ml=total_intake,
        remaining_ml=remaining
    )


# Reset daily intake
@router.post("/reset")
async def reset_water_intake(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    await db.execute(
        delete(WaterIntake).where(WaterIntake.user_id == user_id, WaterIntake.date == date.today())
    )
    await db.commit()
    return {"message": "Daily intake reset"}
