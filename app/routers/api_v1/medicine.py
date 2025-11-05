import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.medicine import Medicine, MedicineIntakeHistory, MedicineSchedule, MedicineHistory
from app.schemas.medicine import MedicineIntakeCreate, MedicineIntakeRead, MedicineRead, MedicineCreate, MedicineScheduleRead, MedicineUpdate

router = APIRouter(prefix="/api/v1/medicine", tags=["Medicine"])


@router.post("/", response_model=MedicineRead)
async def create_medicine(
    request: Request,
    payload: MedicineCreate,
    db: AsyncSession = Depends(get_db)
):
    user_id = getattr(request.state, "user_id", None)
    medicine = Medicine(
        user_id=user_id,
        name=payload.name,
        dosage=payload.dosage,
        notes=payload.notes,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    db.add(medicine)
    await db.flush()

    for s in payload.schedules:
        schedule = MedicineSchedule(
            medicine_id=medicine.id,
            user_id=user_id,
            time_of_day=s.time_of_day,
            dose_label=s.dose_label,
            dosage=s.dosage,
        )
        db.add(schedule)

    await db.commit()
    await db.refresh(medicine)
    return medicine


@router.get("/", response_model=list[MedicineRead])
async def get_medicines(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user_id = getattr(request.state, "user_id", None)
    result = await db.execute(select(Medicine)
                              .options(selectinload(Medicine.schedules))
                              .where(Medicine.user_id == user_id))
    return result.scalars().unique().all()


@router.put("/{medicine_id}", response_model=MedicineRead)
async def update_medicine(
    request: Request,
    medicine_id: str,
    payload: MedicineUpdate,
    db: AsyncSession = Depends(get_db)
):
    user_id = getattr(request.state, "user_id", None)

    # Fetch the medicine with schedules eagerly loaded
    result = await db.execute(
        select(Medicine)
        .options(selectinload(Medicine.schedules))
        .where(Medicine.id == medicine_id, Medicine.user_id == user_id)
    )
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    # --- Track simple field changes ---
    for field, new_value in payload.dict(exclude_unset=True, exclude={"schedules"}).items():
        old_value = getattr(medicine, field, None)
        if old_value != new_value:
            history = MedicineHistory(
                medicine_id=medicine.id,
                user_id=user_id,
                change_type=f"{field}_changed",
                old_value=str(old_value),
                new_value=str(new_value)
            )
            db.add(history)
            setattr(medicine, field, new_value)

    # --- Track schedule changes ---
    if payload.schedules:
        # Convert time objects to strings for JSON serialization
        old_schedules = [
            {
                "time_of_day": s.time_of_day.isoformat(),
                "dose_label": s.dose_label,
                "dosage": s.dosage
            }
            for s in medicine.schedules
        ]
        new_schedules = [
            {
                "time_of_day": s.time_of_day.isoformat(),
                "dose_label": s.dose_label,
                "dosage": s.dosage
            }
            for s in payload.schedules
        ]

        # Add history if schedules changed
        if old_schedules != new_schedules:
            history = MedicineHistory(
                medicine_id=medicine.id,
                user_id=user_id,
                change_type="schedules_changed",
                old_value=json.dumps(old_schedules),
                new_value=json.dumps(new_schedules)
            )
            db.add(history)

        # Delete old schedules and add new ones
        await db.execute(
            delete(MedicineSchedule).where(MedicineSchedule.medicine_id == medicine_id)
        )
        for s in payload.schedules:
            db.add(
                MedicineSchedule(
                    medicine_id=medicine.id,
                    user_id=user_id,
                    time_of_day=s.time_of_day,
                    dose_label=s.dose_label,
                    dosage=s.dosage
                )
            )

    # Commit all changes
    await db.commit()
    await db.refresh(medicine)  # Refresh to get updated values

    # --- Prepare response safely ---
    schedules_list = [
        MedicineScheduleRead(
            id=s.id,
            time_of_day=s.time_of_day,
            dose_label=s.dose_label,
            dosage=s.dosage
        ) for s in medicine.schedules
    ]

    response = MedicineRead(
        id=medicine.id,
        name=medicine.name,
        dosage=medicine.dosage,
        schedules=schedules_list
    )
    return response


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


@router.post("/{medicine_id}/status", response_model=MedicineIntakeRead)
async def mark_medicine_status(
    request: Request,
    medicine_id: str,
    payload: MedicineIntakeCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Record when a user marks a medicine as taken/missed/delayed.
    """
    # Ensure medicine exists for current user
    user_id = getattr(request.state, "user_id", None)
    result = await db.execute(
        select(Medicine).where(Medicine.id == medicine_id, Medicine.user_id == user_id)
    )
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")

    intake = MedicineIntakeHistory(
        user_id=user_id,
        medicine_id=medicine.id,
        schedule_id=payload.schedule_id,
        status=payload.status,
        note=payload.note,
    )

    db.add(intake)
    await db.commit()
    await db.refresh(intake)
    return intake


@router.get("/{medicine_id}/history", response_model=list[MedicineIntakeRead])
async def get_medicine_history(
    request: Request,
    medicine_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all intake history for a specific medicine.
    """
    user_id = getattr(request.state, "user_id", None)
    q = select(MedicineIntakeHistory).where(
        MedicineIntakeHistory.medicine_id == medicine_id,
        MedicineIntakeHistory.user_id == user_id,
    ).order_by(MedicineIntakeHistory.taken_at.desc())

    res = await db.execute(q)
    return res.scalars().all()
