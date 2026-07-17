from datetime import date as date_type

from sqlalchemy import String, Integer, ForeignKey, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base, TimestampedMixin, UUIDPKMixin


class XPLog(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "xp_logs"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)


class Level(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "levels"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    current_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Badge(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "badges"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="🏅", nullable=False)


class UserBadge(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "user_badges"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    badge_id: Mapped[str] = mapped_column(String(36), ForeignKey("badges.id"), nullable=False, index=True)


class Streak(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "streaks"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    streak_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    current_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_active_date: Mapped[date_type | None] = mapped_column(Date, nullable=True)


class Penalty(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "penalties"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
