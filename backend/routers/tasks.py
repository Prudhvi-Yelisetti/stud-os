from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.tasks import Task, TaskStatus, TaskPriority, Subtask, RepeatRule
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.tasks import TaskCreate, TaskUpdate, TaskOut, TaskCompleteResponse, GamificationEventOut
from backend.schemas.projects import SubtaskCreate, SubtaskUpdate, SubtaskOut
from backend.gamification.engine import on_task_completed
from backend.gamification.penalties import check_and_apply_overdue_penalties
from backend.utils.recurrence import next_occurrence

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Native enum columns sort alphabetically by their stored string value in
# SQL, not by logical severity ("high" sorts after "low" alphabetically).
# This case expression maps each value to its actual priority weight so
# `.order_by(PRIORITY_WEIGHT.desc())` reflects real urgency, not the alphabet.
PRIORITY_WEIGHT = case(
    (Task.priority == TaskPriority.urgent, 4),
    (Task.priority == TaskPriority.high, 3),
    (Task.priority == TaskPriority.medium, 2),
    (Task.priority == TaskPriority.low, 1),
    else_=0,
)


def _get_task_or_404(db: Session, task_id: str, user: User) -> Task:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.user_id == user.id, Task.is_trashed.is_(False))
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: TaskStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    check_and_apply_overdue_penalties(db, user.id)

    q = db.query(Task).filter(Task.user_id == user.id, Task.is_trashed.is_(False))
    if status is not None:
        q = q.filter(Task.status == status)
    return q.order_by(
        PRIORITY_WEIGHT.desc(),
        Task.due_at.is_(None),  # tasks with a due date sort before those without
        Task.due_at.asc(),
        Task.created_at.desc(),
    ).all()


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = Task(user_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: str, payload: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    task = _get_task_or_404(db, task_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def trash_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = _get_task_or_404(db, task_id, user)
    task.is_trashed = True
    task.trashed_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/{task_id}/complete", response_model=TaskCompleteResponse)
def complete_task(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = _get_task_or_404(db, task_id, user)
    if task.status == TaskStatus.done:
        raise HTTPException(status_code=400, detail="Task already completed")

    task.status = TaskStatus.done
    task.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    result = on_task_completed(db, user.id, task.priority)

    if task.repeat_rule != RepeatRule.none:
        base = task.due_at or task.scheduled_at or datetime.now(timezone.utc)
        next_due = next_occurrence(task.repeat_rule, base)
        next_scheduled = (
            next_occurrence(task.repeat_rule, task.scheduled_at) if task.scheduled_at else None
        )
        db.add(
            Task(
                user_id=user.id,
                project_id=task.project_id,
                title=task.title,
                description=task.description,
                priority=task.priority,
                repeat_rule=task.repeat_rule,
                scheduled_at=next_scheduled,
                due_at=next_due,
                status=TaskStatus.todo,
            )
        )
        db.commit()

    return TaskCompleteResponse(
        task=TaskOut.model_validate(task),
        gamification=GamificationEventOut(
            xp_awarded=result.xp_awarded,
            current_xp=result.level.current_xp,
            current_level=result.level.current_level,
            did_level_up=result.did_level_up,
            streak_count=result.streak.current_count,
            newly_awarded_badges=result.newly_awarded_badges,
        ),
    )


@router.get("/{task_id}/subtasks", response_model=list[SubtaskOut])
def list_subtasks(task_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_task_or_404(db, task_id, user)
    return db.query(Subtask).filter(Subtask.task_id == task_id).order_by(Subtask.created_at).all()


@router.post("/{task_id}/subtasks", response_model=SubtaskOut, status_code=201)
def create_subtask(
    task_id: str, payload: SubtaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _get_task_or_404(db, task_id, user)
    subtask = Subtask(task_id=task_id, title=payload.title)
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskOut)
def update_subtask(subtask_id: str, payload: SubtaskUpdate, db: Session = Depends(get_db)):
    subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if subtask is None:
        raise HTTPException(status_code=404, detail="Subtask not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subtask, field, value)
    db.commit()
    db.refresh(subtask)
    return subtask


@router.delete("/subtasks/{subtask_id}", status_code=204)
def delete_subtask(subtask_id: str, db: Session = Depends(get_db)):
    subtask = db.query(Subtask).filter(Subtask.id == subtask_id).first()
    if subtask is None:
        raise HTTPException(status_code=404, detail="Subtask not found")
    db.delete(subtask)
    db.commit()
