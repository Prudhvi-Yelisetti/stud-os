from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.database.models.tasks import TaskStatus, TaskPriority, RepeatRule


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    project_id: str | None = None
    priority: TaskPriority = TaskPriority.medium
    repeat_rule: RepeatRule = RepeatRule.none
    scheduled_at: datetime | None = None
    due_at: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    repeat_rule: RepeatRule | None = None
    scheduled_at: datetime | None = None
    due_at: datetime | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    repeat_rule: RepeatRule
    scheduled_at: datetime | None
    due_at: datetime | None
    completed_at: datetime | None
    is_penalized: bool
    created_at: datetime
    updated_at: datetime


class GamificationEventOut(BaseModel):
    xp_awarded: int
    current_xp: int
    current_level: int
    did_level_up: bool
    streak_count: int
    newly_awarded_badges: list[str]


class TaskCompleteResponse(BaseModel):
    task: TaskOut
    gamification: GamificationEventOut
