from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declared_attr


class TimestampMixin:
    """Mixin to add created, updated, and deleted timestamps."""

    @declared_attr
    def created_at(cls):
        """Timestamp when the record was created."""
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        """Timestamp when the record was last updated."""
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @declared_attr
    def deleted_at(cls):
        """Timestamp when the record was soft-deleted (NULL means active)."""
        return Column(DateTime(timezone=True), nullable=True)
