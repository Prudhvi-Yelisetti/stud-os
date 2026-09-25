from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database.session import get_db
from backend.database.models.notes import Chapter, Notebook
from backend.database.models.tasks import Task
from backend.database.models.journal import JournalEntry
from backend.database.models.tags import Tag, TagLink
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.ai.indexing import semantic_search as run_semantic_search
from backend.utils.search_query import parse_query

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


def _tagged_ids(db: Session, taggable_type: str, tag_names: list[str]) -> set[str]:
    """IDs of taggable_type entities carrying any of the given tag names
    (case-insensitive substring, matching tag names being lowercased at
    write time in tag_indexing.reindex_tags)."""
    if not tag_names:
        return set()
    rows = (
        db.query(TagLink.taggable_id)
        .join(Tag, Tag.id == TagLink.tag_id)
        .filter(TagLink.taggable_type == taggable_type, or_(*[Tag.name.ilike(f"%{t}%") for t in tag_names]))
        .all()
    )
    return {r.taggable_id for r in rows}


def _excluded_by_words(title: str, body: str, exclude_words: list[str]) -> bool:
    haystack = f"{title}\n{body}".lower()
    return any(w.lower() in haystack for w in exclude_words)


@router.get("", response_model=list[SearchResult])
def search(q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Literal/keyword search across notebooks, chapters, tasks, and journal
    entries -- plus Obsidian-style operators (see utils/search_query.py):
    `tag:x`, `-tag:x`, `notebook:x`, `-notebook:x`, and a bare `-word` to
    exclude. tag:/notebook: only apply to result types that have a tag or
    a parent notebook (chapters and journal entries for tags; chapters
    only for notebook) -- notebooks and tasks are simply left out of the
    results when either operator is active, rather than silently ignoring
    it for them. For meaning-based search over notes/journal content, see
    GET /api/search/semantic.
    """
    if not q or len(q.strip()) < 2:
        return []
    parsed = parse_query(q.strip())
    has_tag_filter = bool(parsed.tags or parsed.exclude_tags)
    has_notebook_filter = bool(parsed.notebooks or parsed.exclude_notebooks)
    like = f"%{parsed.text}%" if parsed.text else None
    results: list[SearchResult] = []

    if like and not has_tag_filter and not has_notebook_filter:
        notebooks = (
            db.query(Notebook)
            .filter(Notebook.user_id == user.id, Notebook.is_trashed.is_(False), Notebook.title.ilike(like))
            .limit(10)
            .all()
        )
        results += [SearchResult(type="notebook", id=nb.id, title=nb.title) for nb in notebooks]

    chapter_query = (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_trashed.is_(False))
    )
    if like:
        chapter_query = chapter_query.filter(or_(Chapter.title.ilike(like), Chapter.content.ilike(like)))
    if parsed.notebooks:
        chapter_query = chapter_query.filter(or_(*[Notebook.title.ilike(f"%{n}%") for n in parsed.notebooks]))
    for n in parsed.exclude_notebooks:
        chapter_query = chapter_query.filter(~Notebook.title.ilike(f"%{n}%"))
    if parsed.tags:
        chapter_query = chapter_query.filter(Chapter.id.in_(_tagged_ids(db, "chapter", parsed.tags)))
    for excluded_id in _tagged_ids(db, "chapter", parsed.exclude_tags):
        chapter_query = chapter_query.filter(Chapter.id != excluded_id)
    # A pure exclude-only query (e.g. just "-someword", no positive
    # selector at all) has nothing to select FOR -- don't fall through to
    # returning up to 15 arbitrary chapters.
    if like or parsed.tags or parsed.notebooks:
        chapters = chapter_query.limit(15).all()
        results += [
            SearchResult(type="chapter", id=ch.id, title=ch.title, snippet=ch.content[:120])
            for ch in chapters
            if not _excluded_by_words(ch.title, ch.content, parsed.exclude_words)
        ]

    if like and not has_tag_filter and not has_notebook_filter:
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
        results += [
            SearchResult(type="task", id=t.id, title=t.title)
            for t in tasks
            if not _excluded_by_words(t.title, t.description or "", parsed.exclude_words)
        ]

    if not has_notebook_filter:  # journal entries have no notebook, but ARE taggable
        entry_query = db.query(JournalEntry).filter(
            JournalEntry.user_id == user.id, JournalEntry.is_trashed.is_(False)
        )
        if like:
            entry_query = entry_query.filter(or_(JournalEntry.title.ilike(like), JournalEntry.content.ilike(like)))
        if parsed.tags:
            entry_query = entry_query.filter(JournalEntry.id.in_(_tagged_ids(db, "journal", parsed.tags)))
        for excluded_id in _tagged_ids(db, "journal", parsed.exclude_tags):
            entry_query = entry_query.filter(JournalEntry.id != excluded_id)
        if like or parsed.tags:  # otherwise there's no positive selector at all -- don't return everything
            entries = entry_query.limit(15).all()
            results += [
                SearchResult(type="journal", id=e.id, title=e.title, snippet=e.content[:120])
                for e in entries
                if not _excluded_by_words(e.title, e.content, parsed.exclude_words)
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
