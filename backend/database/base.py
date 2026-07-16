"""
Declarative base + shared model mixin for Stud-OS.

Every table gets id / created_at / updated_at / soft-delete fields from
this mixin from day one. Last time these were retrofitted per-entity
across multiple migrations (add_trash_flags, then
add_whiteboard_trash_flags) -- baking it in here avoids repeating that.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, Boolean, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampedMixin:
    """created_at / updated_at, present on every table."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class SoftDeleteMixin:
    """Soft-delete flag, present on every trashable table from day one."""

    is_trashed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trashed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class UUIDPKMixin:
    """UUID string primary key, shared across all entities."""

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
