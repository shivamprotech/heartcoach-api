"""Remove MedicineIntake table and create DailyMedicineIntake

Revision ID: d87674b70a54
Revises: d3f0d9b4547b
Create Date: 2025-11-15 14:00:11.795747
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d87674b70a54"
down_revision: Union[str, Sequence[str], None] = "d3f0d9b4547b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1) Extend existing enum type with the new value 'pending'
    #    (old type likely had 'taken', 'missed', 'delayed')
    op.execute("ALTER TYPE intake_status ADD VALUE IF NOT EXISTS 'pending'")

    # 2) Reuse existing enum type in the new table (do NOT create it again)
    intake_status_enum = postgresql.ENUM(
        "pending",
        "taken",
        "missed",
        "delayed",
        name="intake_status",
        create_type=False,  # <- important: don't emit CREATE TYPE
    )

    # 3) Create new table using the existing enum type
    op.create_table(
        "daily_medicine_intakes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("schedule_id", sa.UUID(), nullable=False),
        sa.Column("intake_date", sa.Date(), nullable=False),
        sa.Column("status", intake_status_enum, nullable=False),
        sa.Column(
            "status_changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("scheduled_time", sa.Time(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["schedule_id"], ["medicine_schedules.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "schedule_id",
            "intake_date",
            name="uq_daily_intake_schedule_date",
        ),
    )

    op.create_index(
        "ix_daily_intake_user_date",
        "daily_medicine_intakes",
        ["user_id", "intake_date"],
        unique=False,
    )

    # 4) Drop old tables that used to store intake
    op.drop_table("medicine_history")
    op.drop_table("medicine_intake_history")


def downgrade() -> None:
    """Downgrade schema."""

    # Recreate old tables (schema from autogenerate)
    op.create_table(
        "medicine_intake_history",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("medicine_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("schedule_id", sa.UUID(), autoincrement=False, nullable=True),
        sa.Column("note", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "taken_at",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "deleted_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["medicine_id"],
            ["medicines.id"],
            name=op.f("medicine_intake_history_medicine_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["schedule_id"],
            ["medicine_schedules.id"],
            name=op.f("medicine_intake_history_schedule_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("medicine_intake_history_user_id_fkey"),
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("medicine_intake_history_pkey")
        ),
    )

    op.create_table(
        "medicine_history",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("medicine_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("change_type", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("old_value", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("new_value", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "changed_at",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "deleted_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["medicine_id"],
            ["medicines.id"],
            name=op.f("medicine_history_medicine_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("medicine_history_user_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("medicine_history_pkey")),
    )

    op.drop_index("ix_daily_intake_user_date", table_name="daily_medicine_intakes")
    op.drop_table("daily_medicine_intakes")
    # NOTE: we do NOT drop the type 'intake_status' here,
    # because older migrations / tables may still rely on it.
