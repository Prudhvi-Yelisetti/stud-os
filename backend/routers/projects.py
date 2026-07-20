from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.projects import Project
from backend.database.models.tasks import Task, TaskStatus, Subtask
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.projects import (
    ProjectCreate, ProjectUpdate, ProjectOut, SubtaskCreate, SubtaskUpdate, SubtaskOut,
)
from backend.schemas.tasks import TaskOut

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Same alphabetical-sort pitfall as priority (see routers/tasks.py) --
# "done" sorts before "todo" alphabetically, which would bury active work
# under finished work. Map to an explicit "needs attention" ordering instead.
STATUS_WEIGHT = case(
    (Task.status == TaskStatus.in_progress, 0),
    (Task.status == TaskStatus.todo, 1),
    (Task.status == TaskStatus.backlog, 2),
    (Task.status == TaskStatus.done, 3),
    else_=4,
)


def _get_project_or_404(db: Session, project_id: str, user: User) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id, Project.is_trashed.is_(False))
        .first()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Project)
        .filter(Project.user_id == user.id, Project.is_trashed.is_(False))
        .order_by(Project.updated_at.desc())
        .all()
    )


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    project = Project(user_id=user.id, **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def trash_project(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = _get_project_or_404(db, project_id, user)
    project.is_trashed = True
    project.trashed_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/{project_id}/tasks", response_model=list[TaskOut])
def list_project_tasks(project_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_project_or_404(db, project_id, user)
    return (
        db.query(Task)
        .filter(Task.project_id == project_id, Task.is_trashed.is_(False))
        .order_by(STATUS_WEIGHT, Task.created_at.desc())
        .all()
    )
