"""update users_info table to add dob, avatar, and enum blood group

Revision ID: 0270396111b7
Revises: 37b20a000e66
Create Date: 2025-11-07 14:24:22.983467
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision: str = '0270396111b7'
down_revision: Union[str, Sequence[str], None] = '37b20a000e66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely by creating enum type and altering column."""
    bind = op.get_bind()

    # 1️⃣ Define enum
    blood_group_enum = sa.Enum(
        'A_POS', 'A_NEG', 'B_POS', 'B_NEG', 'AB_POS', 'AB_NEG', 'O_POS', 'O_NEG',
        name='blood_group_enum'
    )

    # 2️⃣ Create the enum type if it doesn't exist
    blood_group_enum.create(bind, checkfirst=True)

    # 3️⃣ Apply schema changes
    op.add_column('users_info', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('users_info', sa.Column('avatar_url', sa.String(), nullable=True, comment="URL of the user's profile picture"))

    # 4️⃣ Safely alter blood_group column type to enum
    op.alter_column(
        'users_info',
        'blood_group',
        existing_type=sa.VARCHAR(),
        type_=blood_group_enum,
        existing_nullable=True,
        postgresql_using='blood_group::text::blood_group_enum'  # ✅ safer auto-cast
    )

    # 5️⃣ Drop old 'age' column
    op.drop_column('users_info', 'age')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    blood_group_enum = sa.Enum(
        'A_POS', 'A_NEG', 'B_POS', 'B_NEG', 'AB_POS', 'AB_NEG', 'O_POS', 'O_NEG',
        name='blood_group_enum'
    )

    op.add_column('users_info', sa.Column('age', sa.Integer(), nullable=True))

    op.alter_column(
        'users_info',
        'blood_group',
        existing_type=blood_group_enum,
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using='blood_group::text'
    )

    op.drop_column('users_info', 'avatar_url')
    op.drop_column('users_info', 'date_of_birth')

    # Drop enum type (optional, keep if reused elsewhere)
    blood_group_enum.drop(bind, checkfirst=True)
