"""add role column in user table

Revision ID: eea622dc2096
Revises: 0270396111b7
Create Date: 2025-11-07 15:02:05.093669
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eea622dc2096'
down_revision: Union[str, Sequence[str], None] = '0270396111b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Explicitly create the enum type before using it
    user_role_enum = sa.Enum('PATIENT', 'DOCTOR', 'ADMIN', 'GUEST', name='user_role_enum')
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # Now safely add the column using the enum
    op.add_column(
        'users_info',
        sa.Column('role', user_role_enum, nullable=False, server_default='PATIENT')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users_info', 'role')

    # Drop the enum type if not needed elsewhere
    user_role_enum = sa.Enum('PATIENT', 'DOCTOR', 'ADMIN', 'GUEST', name='user_role_enum')
    user_role_enum.drop(op.get_bind(), checkfirst=True)
