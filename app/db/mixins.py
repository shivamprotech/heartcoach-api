from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_continuum import versioning_manager


class AsyncVersionedMixin:
    """
    A mixin to safely fetch version history for versioned models
    when using async SQLAlchemy.
    """

    __abstract__ = True

    @property
    def version_class(self):
        """Get the associated version class for this model."""
        mapper = self.__class__.__mapper__
        return versioning_manager.version_class_map.get(mapper.class_)

    async def get_versions(self, db: AsyncSession):
        """
        Async-safe method to fetch all versions for this entity.
        Equivalent to `self.versions` in sync mode.
        """
        version_cls = self.version_class
        if version_cls is None:
            raise RuntimeError(f"No version class found for {self.__class__.__name__}")

        result = await db.execute(
            select(version_cls)
            .where(version_cls.id == self.id)
            .order_by(version_cls.transaction_id.desc())
        )
        return result.scalars().all()

    async def get_latest_version(self, db: AsyncSession):
        """
        Fetch the latest version (most recent change).
        """
        versions = await self.get_versions(db)
        return versions[0] if versions else None
