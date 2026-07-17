from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.session import get_db
from backend.database.models.notes import Chapter, Notebook
from backend.database.models.tasks import Task
from backend.database.models.journal import JournalEntry
from backend.database.models.user import User
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchResult(BaseModel):
    type: str  # "chapter" | "notebook" | "task" | "journal"
    id: str
    title: str
    snippet: str | None = None


@router.get("", response_model=list[SearchResult])
def search(q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Literal/keyword search across notebooks, chapters, tasks, and journal
    entries. Semantic search (embeddings) is a V2 item -- see REBUILD_PLAN.md.
    """
    if not q or len(q.strip()) < 2:
        return []
    like = f"%{q.strip()}%"
    results: list[SearchResult] = []

    notebooks = (
        db.query(Notebook)
        .filter(Notebook.user_id == user.id, Notebook.is_trashed.is_(False), Notebook.title.ilike(like))
        .limit(10)
        .all()
    )
    results += [SearchResult(type="notebook", id=nb.id, title=nb.title) for nb in notebooks]

    chapters = (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(
            Notebook.user_id == user.id,
            Chapter.is_trashed.is_(False),
            or_(Chapter.title.ilike(like), Chapter.content.ilike(like)),
        )
        .limit(15)
        .all()
    )
    results += [
        SearchResult(type="chapter", id=ch.id, title=ch.title, snippet=ch.content[:120]) for ch in chapters
    ]

    tasks = (
        db.query(Task)
        .filter(
            Task.user_id == user.id,
            Task.is_trashed.is_(False),
            or_(Task.title.ilike(like), Task.description.ilike(like)),
        )
        .limit(15)
        .all()
    )
    results += [SearchResult(type="task", id=t.id, title=t.title) for t in tasks]

    entries = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.user_id == user.id,
            JournalEntry.is_trashed.is_(False),
            or_(JournalEntry.title.ilike(like), JournalEntry.content.ilike(like)),
        )
        .limit(15)
        .all()
    )
    results += [
        SearchResult(type="journal", id=e.id, title=e.title, snippet=e.content[:120]) for e in entries
    ]

    return results
