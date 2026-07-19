from datetime import datetime, timezone

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.notes import Notebook, Chapter
from backend.database.models.tasks import Task
from backend.database.models.journal import JournalEntry
from backend.database.models.projects import Project
from backend.database.models.user import User
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/trash", tags=["trash"])

TRASHABLE = {
    "notebook": Notebook,
    "chapter": Chapter,
    "task": Task,
    "journal": JournalEntry,
    "project": Project,
}


class TrashedItem(BaseModel):
    type: str
    id: str
    title: str
    trashed_at: datetime | None


@router.get("", response_model=list[TrashedItem])
def list_trash(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items: list[TrashedItem] = []

    for type_name in ("notebook", "task", "journal", "project"):
        model = TRASHABLE[type_name]
        rows = db.query(model).filter(model.user_id == user.id, model.is_trashed.is_(True)).all()
        items += [TrashedItem(type=type_name, id=r.id, title=r.title, trashed_at=r.trashed_at) for r in rows]

    # Chapter has no user_id of its own -- scope through its notebook.
    chapters = (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_trashed.is_(True))
        .all()
    )
    items += [TrashedItem(type="chapter", id=c.id, title=c.title, trashed_at=c.trashed_at) for c in chapters]

    items.sort(key=lambda i: i.trashed_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return items


@router.post("/{item_type}/{item_id}/restore", response_model=TrashedItem)
def restore_item(item_type: str, item_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if item_type not in TRASHABLE:
        raise HTTPException(status_code=400, detail=f"Unknown type '{item_type}'")

    model = TRASHABLE[item_type]

    if item_type == "chapter":
        item = (
            db.query(Chapter)
            .join(Notebook, Notebook.id == Chapter.notebook_id)
            .filter(Chapter.id == item_id, Notebook.user_id == user.id)
            .first()
        )
    else:
        item = db.query(model).filter(model.id == item_id, model.user_id == user.id).first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    item.is_trashed = False
    item.trashed_at = None
    db.commit()
    db.refresh(item)
    return TrashedItem(type=item_type, id=item.id, title=item.title, trashed_at=item.trashed_at)


@router.delete("/{item_type}/{item_id}", status_code=204)
def permanently_delete(item_type: str, item_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Permanently remove a trashed item. Irreversible."""
    if item_type not in TRASHABLE:
        raise HTTPException(status_code=400, detail=f"Unknown type '{item_type}'")

    model = TRASHABLE[item_type]

    if item_type == "chapter":
        item = (
            db.query(Chapter)
            .join(Notebook, Notebook.id == Chapter.notebook_id)
            .filter(Chapter.id == item_id, Notebook.user_id == user.id)
            .first()
        )
    else:
        item = db.query(model).filter(model.id == item_id, model.user_id == user.id).first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
