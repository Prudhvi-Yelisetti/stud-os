import enum
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampedMixin, SoftDeleteMixin, UUIDPKMixin


class TaskStatus(str, enum.Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class RepeatRule(str, enum.Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class Task(Base, UUIDPKMixin, TimestampedMixin, SoftDeleteMixin):
    __tablename__ = "tasks"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.todo, nullable=False, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.medium, nullable=False
    )
    repeat_rule: Mapped[RepeatRule] = mapped_column(
        Enum(RepeatRule), default=RepeatRule.none, nullable=False
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_penalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    subtasks: Mapped[list["Subtask"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class Subtask(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "subtasks"

    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="subtasks")
