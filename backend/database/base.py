"""
Declarative base + shared model mixin for Stud-OS.

Every table gets id / created_at / updated_at / soft-delete fields from
this mixin from day one. Last time these were retrofitted per-entity
across multiple migrations (add_trash_flags, then
add_whiteboard_trash_flags) -- baking it in here avoids repeating that.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, String, DateTime, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """DateTime(timezone=True), but actually round-trips as UTC-aware --
    on SQLite (this app's only backend), a plain DateTime(timezone=True)
    silently drops tzinfo on read despite the flag. That's not just a
    Python-level footgun (comparing the result to an aware datetime
    raises TypeError); it also meant every timestamp got serialized to
    the frontend as an ISO string with no UTC marker at all (e.g.
    "2026-08-14T01:00:00" instead of "...+00:00"). A bare marker-less
    ISO string is parsed by JS `new Date(...)` as LOCAL time, not UTC --
    so due dates and "overdue" highlighting were silently wrong by
    whatever the browser's UTC offset happens to be, for anyone not
    physically in UTC. Every datetime this app stores is always UTC by
    convention (see _utcnow above) -- fixed once here, for every table
    that uses it, rather than patching call sites as this kept surfacing.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampedMixin:
    """created_at / updated_at, present on every table."""

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )


class SoftDeleteMixin:
    """Soft-delete flag, present on every trashable table from day one."""

    is_trashed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trashed_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime, nullable=True
    )


class UUIDPKMixin:
    """UUID string primary key, shared across all entities."""

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
