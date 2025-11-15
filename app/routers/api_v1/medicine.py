
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_medicine_repo, get_medicine_service, get_user_id
from app.core.logging import setup_logger
from app.db.session import get_db
from app.models.medicine import DailyMedicineIntake, Medicine, MedicineSchedule
from app.repositories.medicine_repo import MedicineRepository
from app.schemas.medicine import (MedicineIntakeCreate, MedicineIntakeRead, MedicineRead, MedicineCreate,
                                  MedicineScheduleRead, MedicineScheduleUpdate, MedicineUpdate)
from app.services.medicine_service import MedicineService

router = APIRouter(prefix="/api/v1/medicine", tags=["Medicine"])

logger = setup_logger()


@router.post("/", response_model=MedicineRead)
async def create_medicine(
    payload: MedicineCreate,
    user_id: str = Depends(get_user_id),
    medicine_service: MedicineService = Depends(get_medicine_service)
):
    """
    Create a new medicine and its associated schedules.

    This endpoint creates a new medicine entry for the authenticated user
    along with one or more schedules (e.g., morning, evening doses).

    :param medicine: The medicine creation payload
    :type medicine: MedicineCreate
    :param user_id: The authenticated user's ID
    :type user_id: UUID
    :param db: The database session
    :type db: AsyncSession
    :raises HTTPException: 500 if creation fails
    :return: The created medicine with its schedules
    :rtype: MedicineResponse
    """
    try:
        created_medicine = await medicine_service.create_medicine(user_id, payload)
        return created_medicine
    except Exception as e:
        logger.error(f"Error creating medicine for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create medicine")


@router.get("/", response_model=list[MedicineRead])
async def get_medicines(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
    medicine_repo: MedicineRepository = Depends(get_medicine_repo),
):
    """
    Retrieve all medicines and their schedules for the authenticated user.

    :param user_id: The unique identifier (UUID) of the authenticated user, extracted from the token.
    :type user_id: str
    :param medicine_repo: The repository instance handling medicine database operations.
    :type medicine_repo: MedicineRepository
    :return: A list of medicines with their associated schedules.
    :rtype: list[MedicineRead]
    :raises HTTPException: If the retrieval fails due to a database or internal error.
    """
    logger.info(f"Fetching medicines for user_id={user_id}")

    try:
        medicines = await medicine_repo.get_medicines(user_id)
        if medicines:
            logger.info(f"Successfully retrieved {len(medicines)} medicines for user_id={user_id}")
        else:
            logger.warning(f"No medicines found for user_id={user_id}")

        return medicines

    except Exception as e:
        logger.error(f"Error fetching medicines for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch medicines")


@router.put("/{medicine_id}", response_model=MedicineRead)
async def update_medicine(
    medicine_id: UUID,
    payload: MedicineUpdate,
    medicine_service: MedicineService = Depends(get_medicine_service),
    user_id: UUID = Depends(get_user_id),
):
    """
    Update medicine details; changes are auto-tracked via SQLAlchemy-Continuum.
    """
    try:
        medicine = await medicine_service.update_medicine(user_id=user_id, medicine_id=medicine_id, payload=payload)
        return medicine
    except Exception as e:
        logger.error(f"Error fetching medicines for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch medicines")


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medicine(
    request: Request,
    medicine_id: str,
    db: AsyncSession = Depends(get_db),
):
    user_id = getattr(request.state, "user_id", None)
    result = await db.execute(select(Medicine).where(Medicine.id == medicine_id, Medicine.user_id == user_id))
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    await db.delete(medicine)
    await db.commit()
    return {"detail": "Medicine deleted"}


@router.get("/{medicine_id}/schedule", response_model=list[MedicineScheduleRead])
async def get_medicine_schedules(
    medicine_id: UUID,
    user_id: UUID = Depends(get_user_id),
    medicine_repo: MedicineRepository = Depends(get_medicine_repo),
):
    """
    Retrieve all medicines and their schedules for the authenticated user.

    :param user_id: The unique identifier (UUID) of the authenticated user, extracted from the token.
    :type user_id: str
    :param medicine_repo: The repository instance handling medicine database operations.
    :type medicine_repo: MedicineRepository
    :return: A list of medicines with their associated schedules.
    :rtype: list[MedicineRead]
    :raises HTTPException: If the retrieval fails due to a database or internal error.
    """
    logger.info(f"Fetching schedule for medicine_id={medicine_id} and user_id={user_id}")

    try:
        schedule = await medicine_repo.get_medicine_schedules(user_id=user_id, medicine_id=medicine_id)

        if schedule:
            logger.info(f"Successfully retrieved {len(schedule)} schedule for medicine_id={medicine_id}")
        else:
            logger.warning(f"No schedule found for medicine_id={medicine_id}")

        return schedule

    except Exception as e:
        logger.error(f"Error fetching schedule for medicine_id={medicine_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch schedule")


@router.put("/schedule/{schedule_id}", response_model=MedicineRead)
async def update_schedule(
    schedule_id: UUID,
    payload: MedicineScheduleUpdate,
    user_id: str = Depends(get_user_id),
    medicine_service: MedicineService = Depends(get_medicine_service),
):
    """
    Update a specific medicine schedule for the authenticated user.

    :param schedule_id: UUID of the schedule to be updated.
    :param payload: Updated schedule details.
    :param user_id: ID of the authenticated user.
    :return: Updated Medicine with all schedules.
    """
    logger.info(f"Updating medicine schedule {schedule_id} for user_id={user_id}")
    try:
        updated_medicine = await medicine_service.update_medicine_schedule(user_id, schedule_id, payload)
        return updated_medicine
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule {schedule_id} for user_id={user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update medicine schedule")


@router.post("/{medicine_id}/status", response_model=MedicineIntakeRead)
async def mark_medicine_status(
    request: Request,
    medicine_id: str,
    payload: MedicineIntakeCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Record/update the daily intake status for a specific medicine schedule.

    - Validates that the medicine belongs to the current user.
    - Validates that the schedule belongs to that medicine & user.
    - Upserts a DailyMedicineIntake row for (user, schedule, intake_date).
    """

    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 1) Ensure medicine exists for this user
    result = await db.execute(
        select(Medicine).where(
            Medicine.id == medicine_id,
            Medicine.user_id == user_id,
        )
    )
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    # 2) Ensure schedule belongs to this medicine & user
    if not payload.schedule_id:
        raise HTTPException(status_code=400, detail="schedule_id is required")

    result = await db.execute(
        select(MedicineSchedule).where(
            MedicineSchedule.id == payload.schedule_id,
            MedicineSchedule.user_id == user_id,
            MedicineSchedule.medicine_id == medicine.id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found for this medicine")

    # 3) Determine intake_date (user's "today" or provided explicitly)
    intake_date = payload.intake_date or date.today()

    # Enforce medicine start/end window
    if medicine.start_date and intake_date < medicine.start_date:
        raise HTTPException(status_code=400, detail="Intake date is before medicine start date")

    if medicine.end_date and intake_date > medicine.end_date:
        raise HTTPException(status_code=400, detail="Intake date is after medicine end date")

    # 4) Upsert DailyMedicineIntake for (user, schedule, intake_date)
    result = await db.execute(
        select(DailyMedicineIntake).where(
            DailyMedicineIntake.user_id == user_id,
            DailyMedicineIntake.schedule_id == schedule.id,
            DailyMedicineIntake.intake_date == intake_date,
        )
    )
    intake = result.scalar_one_or_none()

    now = func.now()

    if intake is None:
        # Create new daily record
        intake = DailyMedicineIntake(
            user_id=user_id,
            schedule_id=schedule.id,
            intake_date=intake_date,
            status=payload.status,  # IntakeStatus
            status_changed_at=now,
            scheduled_time=schedule.time_of_day,
            note=payload.note,
        )
        db.add(intake)
    else:
        # Update existing daily record status
        intake.status = payload.status
        intake.status_changed_at = now
        intake.note = payload.note

    await db.commit()
    await db.refresh(intake)

    return intake
