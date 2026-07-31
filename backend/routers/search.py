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
from backend.ai.indexing import semantic_search as run_semantic_search

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchResult(BaseModel):
    type: str  # "chapter" | "notebook" | "task" | "journal"
    id: str
    title: str
    snippet: str | None = None


class SemanticSearchResult(BaseModel):
    type: str  # "chapter" | "journal" -- the only indexed parent types today
    id: str
    title: str
    snippet: str
    score: float


@router.get("", response_model=list[SearchResult])
def search(q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Literal/keyword search across notebooks, chapters, tasks, and journal
    entries. For meaning-based search over notes/journal content, see
    GET /api/search/semantic.
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


@router.get("/semantic", response_model=list[SemanticSearchResult])
def semantic_search_endpoint(
    q: str, limit: int = 10, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Meaning-based search over note and journal content, using locally
    generated embeddings (see backend/ai/) -- finds relevant content even
    when the query doesn't share exact words with it. Complements the
    keyword search above.
    """
    if not q or not q.strip():
        return []

    # Over-fetch: some top-scoring chunks may belong to a since-trashed
    # parent (chunks aren't cleaned up on soft-delete, only on permanent
    # delete -- see routers/trash.py). Filter those out below rather than
    # teaching the brute-force similarity scan about trash state.
    scored = run_semantic_search(db, user_id=user.id, query=q.strip(), limit=limit * 3)

    live_chapter_ids = {
        row.id for row in db.query(Chapter.id)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_trashed.is_(False))
        .all()
    }
    live_journal_ids = {
        row.id for row in db.query(JournalEntry.id)
        .filter(JournalEntry.user_id == user.id, JournalEntry.is_trashed.is_(False))
        .all()
    }
    live_ids = {"chapter": live_chapter_ids, "journal": live_journal_ids}

    results: list[SemanticSearchResult] = []
    for chunk, score in scored:
        if chunk.parent_id not in live_ids.get(chunk.parent_type, set()):
            continue
        results.append(SemanticSearchResult(
            type=chunk.parent_type,
            id=chunk.parent_id,
            title=chunk.parent_title,
            snippet=chunk.content[:200],
            score=round(score, 4),
        ))
        if len(results) >= limit:
            break

    return results
