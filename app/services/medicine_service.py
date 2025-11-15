from uuid import UUID

from fastapi import HTTPException
from app.core.logging import setup_logger
from app.repositories.medicine_repo import MedicineRepository
from app.schemas.medicine import MedicineCreate, MedicineRead, MedicineScheduleRead, MedicineScheduleUpdate, MedicineUpdate

logger = setup_logger()


class MedicineService:
    """Service layer for medicine management."""

    def __init__(self, repo: MedicineRepository):
        self.repo = repo

    async def create_medicine(self, user_id: UUID, payload: MedicineCreate):
        """Create a medicine and its schedules."""
        data = payload.model_dump(exclude_unset=True)
        return await self.repo.create_medicine_with_schedules(user_id, data)

    async def update_medicine(self, user_id: UUID, medicine_id: UUID, payload: MedicineUpdate):
        """Update a medicine and its schedules."""
        medicine = await self.repo.get_medicine(user_id=user_id, medicine_id=medicine_id)
        if not medicine:
            raise HTTPException(status_code=404, detail="Medicine not found")

        # Apply updates
        for field, value in payload.model_dump(exclude_unset=True, exclude={"schedules"}).items():
            setattr(medicine, field, value)

        # Handle schedules
        if payload.schedules:
            await self.repo.delete_schedules(medicine_id)
            await self.repo.add_schedules(medicine_id, user_id, payload.schedules)

        await self.repo.commit_and_refresh(medicine)

        return self._to_read_schema(medicine)

    async def update_medicine_schedule(
        self, user_id: UUID, schedule_id: UUID, payload: MedicineScheduleUpdate
    ):
        """
        Update a medicine schedule and return the parent medicine with schedules.

        :param user_id: UUID of the user who owns the schedule
        :param schedule_id: UUID of the schedule to update
        :param payload: Update payload for the schedule
        :return: Updated Medicine with schedules
        """
        logger.info(f"Updating schedule_id={schedule_id} for user_id={user_id}")

        # Fetch the schedule with its parent medicine
        medicine_schedule = await self.repo.get_medicine_schedule(user_id=user_id, schedule_id=schedule_id)
        if not medicine_schedule:
            logger.warning(f"Medicine schedule not found: schedule_id={schedule_id}")
            raise HTTPException(status_code=404, detail="Medicine schedule not found")

        # Perform update through repository
        updated_medicine = await self.repo.update_existing_schedule(medicine_schedule, payload)
        logger.info(f"Successfully updated schedule_id={schedule_id} for user_id={user_id}")
        return updated_medicine

    def _to_read_schema(self, medicine: MedicineRead):
        schedules = [
            MedicineScheduleRead(
                id=s.id, time_of_day=s.time_of_day, dose_label=s.dose_label, dosage=s.dosage
            )
            for s in medicine.schedules
        ]
        return {**medicine.__dict__, "schedules": schedules}
