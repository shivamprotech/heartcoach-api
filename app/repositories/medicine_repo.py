from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.core.logging import setup_logger
from app.models.medicine import DailyMedicineIntake, IntakeStatus, Medicine, MedicineSchedule
from app.schemas.medicine import MedicineCreate, MedicineRead, MedicineScheduleBase, MedicineScheduleUpdate

logger = setup_logger()


class MedicineRepository:
    """Repository layer for performing CRUD operations on Medicine."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_medicines(self, user_id: UUID) -> list[Medicine]:
        """
        Retrieve all medicines and their schedules for a specific user,
        and attach today's intake status to each schedule.

        :param user_id: The unique identifier (UUID) of the user whose medicines are to be fetched.
        :type user_id: UUID
        :return: A list of Medicine objects, each including its associated schedules
                 with an attached `status` attribute (IntakeStatus).
        :rtype: list[Medicine]
        :raises Exception: If the database query or fetch operation fails.
        """
        logger.info(f"Fetching medicines and schedules for user_id={user_id}")

        try:
            # 1) Load medicines and schedules
            result = await self.db.execute(
                select(Medicine)
                .options(selectinload(Medicine.schedules))
                .where(Medicine.user_id == user_id)
            )
            medicines: list[Medicine] = result.scalars().unique().all()

            if not medicines:
                logger.warning(f"No medicines found for user_id={user_id}")
                return medicines

            logger.info(
                f"Successfully fetched {len(medicines)} medicines for user_id={user_id}"
            )

            # 2) Collect all schedule IDs
            schedule_ids = [s.id for m in medicines for s in m.schedules]
            if not schedule_ids:
                # No schedules, nothing more to do
                return medicines

            # 3) Determine the date for which we want status (today by default)
            intake_date = date.today()

            # 4) Load daily intakes for these schedules on that date
            intake_result = await self.db.execute(
                select(DailyMedicineIntake).where(
                    DailyMedicineIntake.user_id == user_id,
                    DailyMedicineIntake.schedule_id.in_(schedule_ids),
                    DailyMedicineIntake.intake_date == intake_date,
                )
            )
            intakes: list[DailyMedicineIntake] = intake_result.scalars().all()
            intake_by_schedule_id = {i.schedule_id: i for i in intakes}

            # 5) Attach status onto each schedule object
            #    If no intake exists for today, treat it as PENDING
            for med in medicines:
                for sched in med.schedules:
                    intake = intake_by_schedule_id.get(sched.id)
                    status = intake.status if intake else IntakeStatus.PENDING
                    setattr(sched, "status", status)

            return medicines

        except Exception as e:
            logger.error(
                f"Failed to fetch medicines for user_id={user_id}. Error: {str(e)}"
            )
            raise

    async def get_medicine(self, medicine_id: UUID, user_id: UUID) -> list[Medicine]:
        """
        Retrieve all medicines and their schedules for a specific user.

        :param user_id: The unique identifier (UUID) of the user whose medicines are to be fetched.
        :type user_id: UUID
        :return: A list of Medicine objects, each including its associated schedules.
        :rtype: list[Medicine]
        :raises Exception: If the database query or fetch operation fails.
        """
        logger.info(f"Fetching medicines and schedules for user_id={user_id}")

        try:
            query = await self.db.execute(
                select(Medicine)
                .options(selectinload(Medicine.schedules))
                .where(Medicine.id == medicine_id, Medicine.user_id == user_id)
            )
            medicine = query.scalar_one_or_none()

            if medicine:
                logger.info(
                    f"Successfully fetched medicine for user_id={user_id}"
                )
            else:
                logger.warning(f"No medicine found for user_id={user_id}")

            return medicine

        except Exception as e:
            logger.error(
                f"Failed to fetch medicines for user_id={user_id}. Error: {str(e)}"
            )
            raise

    async def get_medicine_schedule(self, schedule_id: UUID, user_id: UUID) -> list[Medicine]:
        """
        Retrieve all medicines and their schedules for a specific user.

        :param user_id: The unique identifier (UUID) of the user whose medicines are to be fetched.
        :type user_id: UUID
        :return: A list of Medicine objects, each including its associated schedules.
        :rtype: list[Medicine]
        :raises Exception: If the database query or fetch operation fails.
        """
        logger.info(f"Fetching medicines and schedules for user_id={user_id}")

        try:
            query = await self.db.execute(
                select(MedicineSchedule)
                .where(MedicineSchedule.id == schedule_id, MedicineSchedule.user_id == user_id)
            )
            schedule = query.scalar_one_or_none()

            if schedule:
                logger.info(
                    f"Successfully fetched medicine for user_id={user_id}"
                )
            else:
                logger.warning(f"No medicine found for user_id={user_id}")

            return schedule

        except Exception as e:
            logger.error(
                f"Failed to fetch medicines for user_id={user_id}. Error: {str(e)}"
            )
            raise

    async def get_medicine_schedules(self, medicine_id: UUID, user_id: UUID) -> list[Medicine]:
        """
        Retrieve all medicines and their schedules for a specific user.

        :param user_id: The unique identifier (UUID) of the user whose medicines are to be fetched.
        :type user_id: UUID
        :return: A list of Medicine objects, each including its associated schedules.
        :rtype: list[Medicine]
        :raises Exception: If the database query or fetch operation fails.
        """
        logger.info(f"Fetching medicines and schedules for user_id={user_id}")

        try:
            medicine: MedicineRead = await self.get_medicine(medicine_id=medicine_id, user_id=user_id)

            if medicine.schedules:
                logger.info(
                    f"Successfully fetched medicine for user_id={user_id}"
                )
            else:
                logger.warning(f"No medicine found for user_id={user_id}")

            return medicine.schedules

        except Exception as e:
            logger.error(
                f"Failed to fetch medicines for user_id={user_id}. Error: {str(e)}"
            )
            raise

    async def create_medicine(self, user_id: UUID, medicine: MedicineCreate):
        """
        Create a new medicine along with its schedules for a user.

        :param user_id: UUID of the user creating the medicine
        :type user_id: UUID
        :param medicine: Medicine creation payload (includes optional schedules)
        :type medicine: MedicineCreate
        :return: The newly created Medicine record with schedules loaded
        :rtype: Medicine
        :raises Exception: If the creation or database commit fails
        """
        logger.info(f"Creating medicine for user_id={user_id}")

        try:
            # Convert pydantic model to dictionary (exclude unset fields)
            data = medicine.model_dump(exclude_unset=True)
            created_medicine = await self.repo.create_medicine_with_schedules(user_id, data)

            logger.info(f"Successfully created medicine for user_id={user_id}, id={created_medicine.id}")
            return created_medicine

        except Exception as e:
            logger.error(f"Failed to create medicine for user_id={user_id}: {str(e)}")
            raise

    async def update_medicine(self, user_id, medicine: UUID, payload):
        # Apply scalar updates
        for field, value in payload.model_dump(exclude_unset=True, exclude={"schedules"}).items():
            setattr(medicine, field, value)

        # Update schedules if provided
        if payload.schedules is not None:
            await self.db.execute(delete(MedicineSchedule).where(MedicineSchedule.medicine_id == medicine_id))
            for s in payload.schedules:
                self.db.add(
                    MedicineSchedule(
                        medicine_id=medicine.id,
                        user_id=user_id,
                        time_of_day=s.time_of_day,
                        dose_label=s.dose_label,
                        dosage=s.dosage,
                    )
                )

        await self.db.commit()

        # ✅ Reload with relations to ensure everything is up-to-date
        medicine = await self._reload_with_relations(medicine.id)

        logger.info(f"Medicine updated successfully for user_id={user_id}, medicine_id={medicine.id}")
        return medicine

    async def create_medicine_with_schedules(self, user_id: UUID, medicine_data: dict):
        """
        Create a new medicine and its related schedules in a single transaction.

        :param user_id: UUID of the user who owns this medicine
        :type user_id: UUID
        :param medicine_data: Dictionary containing medicine and schedule details
        :type medicine_data: dict
        :return: Created Medicine object with schedules loaded
        :rtype: Medicine
        :raises Exception: If commit or DB operation fails
        """
        try:
            logger.debug(f"Starting transaction to create medicine for user_id={user_id}")

            # Extract schedules if present
            schedules_data = medicine_data.pop("schedules", [])

            # Create the Medicine record
            medicine = Medicine(user_id=user_id, **medicine_data)
            self.db.add(medicine)
            await self.db.flush()  # Flush to get medicine.id for schedule linking

            # Create related MedicineSchedule records
            for schedule in schedules_data:
                schedule_obj = MedicineSchedule(
                    medicine_id=medicine.id,
                    user_id=user_id,
                    **schedule
                )
                self.db.add(schedule_obj)

            # Commit the transaction
            await self.db.commit()

            # Reload medicine with schedules (to avoid lazy-loading issues)
            result = await self.db.execute(
                select(Medicine)
                .options(selectinload(Medicine.schedules))
                .where(Medicine.id == medicine.id)
            )
            medicine = result.scalars().first()

            logger.info(f"Medicine created successfully for user_id={user_id}, medicine_id={medicine.id}")
            return medicine

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction failed while creating medicine for user_id={user_id}: {str(e)}")
            raise

    async def delete_schedules(self, medicine_id: UUID):
        await self.db.execute(delete(MedicineSchedule).where(MedicineSchedule.medicine_id == medicine_id))

    async def add_schedules(self, medicine_id: UUID, user_id: UUID, schedules: MedicineScheduleBase):
        for s in schedules:
            self.db.add(
                MedicineSchedule(
                    medicine_id=medicine_id,
                    user_id=user_id,
                    time_of_day=s.time_of_day,
                    dose_label=s.dose_label,
                    dosage=s.dosage,
                )
            )

    async def update_existing_schedule(self, schedule: MedicineSchedule, payload: MedicineScheduleUpdate):
        """
        Update a pre-fetched MedicineSchedule and return the parent Medicine with schedules.

        :param schedule: The fetched MedicineSchedule instance
        :param payload: Update data for the schedule
        :return: Updated Medicine instance with schedules
        """
        try:
            data = payload.model_dump(exclude_unset=True)

            # Apply updates in memory
            for field, value in data.items():
                setattr(schedule, field, value)

            await self.db.commit()

            # Reload parent medicine with schedules
            result = await self.db.execute(
                select(Medicine)
                .options(selectinload(Medicine.schedules))
                .where(Medicine.id == schedule.medicine_id)
            )
            updated_medicine = result.scalars().first()

            logger.info(f"Updated existing schedule_id={schedule.id} under medicine_id={schedule.medicine_id}")
            return updated_medicine

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating existing schedule_id={schedule.id}: {str(e)}")
            raise

    async def commit_and_refresh(self, data):
        await self.db.commit()
        await self.db.refresh(data)
