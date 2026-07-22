"""Penalty application for overdue/missed tasks."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.database.models.gamification import Penalty
from backend.database.models.tasks import Task, TaskStatus
from backend.gamification.xp_rules import PENALTY_FOR_OVERDUE_TASK
from backend.gamification.levels import apply_xp


def apply_overdue_penalty(db: Session, user_id: str, task_id: str) -> Penalty:
    penalty = Penalty(
        user_id=user_id,
        task_id=task_id,
        amount=PENALTY_FOR_OVERDUE_TASK,
        reason="Task went overdue",
    )
    db.add(penalty)
    db.commit()
    db.refresh(penalty)
    apply_xp(db, user_id, -PENALTY_FOR_OVERDUE_TASK)
    return penalty


def check_and_apply_overdue_penalties(db: Session, user_id: str) -> int:
    """
    Penalizes every task that's gone overdue since the last check. This was
    previously dead code -- apply_overdue_penalty existed but nothing ever
    called it, so no user could actually be penalized. Called lazily from
    the task-list endpoint (no background scheduler needed for a personal,
    request-driven app) and guarded by is_penalized so a task is only ever
    penalized once. Returns the number of tasks penalized.
    """
    now = datetime.now(timezone.utc)
    overdue_tasks = (
        db.query(Task)
        .filter(
            Task.user_id == user_id,
            Task.is_trashed.is_(False),
            Task.is_penalized.is_(False),
            Task.status != TaskStatus.done,
            Task.due_at.isnot(None),
            Task.due_at < now,
        )
        .all()
    )
    for task in overdue_tasks:
        apply_overdue_penalty(db, user_id, task.id)
        task.is_penalized = True
    if overdue_tasks:
        db.commit()
    return len(overdue_tasks)
