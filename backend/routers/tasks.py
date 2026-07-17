from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.tasks import Task, TaskStatus
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.tasks import TaskCreate, TaskUpdate, TaskOut, TaskCompleteResponse, GamificationEventOut
from backend.gamification.engine import on_task_completed

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


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
    q = db.query(Task).filter(Task.user_id == user.id, Task.is_trashed.is_(False))
    if status is not None:
        q = q.filter(Task.status == status)
    return q.order_by(Task.priority.desc(), Task.created_at.desc()).all()


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
