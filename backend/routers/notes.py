from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.notes import Notebook, Chapter, ChapterLink, ChapterVersion
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.notes import (
    NotebookCreate, NotebookUpdate, NotebookOut,
    ChapterCreate, ChapterUpdate, ChapterOut, BacklinkOut,
)
from backend.utils.wiki_parser import extract_wiki_links

router = APIRouter(prefix="/api/notebooks", tags=["notes"])


def _get_notebook_or_404(db: Session, notebook_id: str, user: User) -> Notebook:
    nb = (
        db.query(Notebook)
        .filter(Notebook.id == notebook_id, Notebook.user_id == user.id, Notebook.is_trashed.is_(False))
        .first()
    )
    if nb is None:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return nb


def _get_chapter_or_404(db: Session, chapter_id: str) -> Chapter:
    ch = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.is_trashed.is_(False)).first()
    if ch is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return ch


@router.get("", response_model=list[NotebookOut])
def list_notebooks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Notebook)
        .filter(Notebook.user_id == user.id, Notebook.is_trashed.is_(False))
        .order_by(Notebook.updated_at.desc())
        .all()
    )


@router.post("", response_model=NotebookOut, status_code=201)
def create_notebook(
    payload: NotebookCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    nb = Notebook(user_id=user.id, title=payload.title, description=payload.description)
    db.add(nb)
    db.commit()
    db.refresh(nb)
    return nb


@router.get("/{notebook_id}", response_model=NotebookOut)
def get_notebook(notebook_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_notebook_or_404(db, notebook_id, user)


@router.patch("/{notebook_id}", response_model=NotebookOut)
def update_notebook(
    notebook_id: str,
    payload: NotebookUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    nb = _get_notebook_or_404(db, notebook_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(nb, field, value)
    db.commit()
    db.refresh(nb)
    return nb


@router.delete("/{notebook_id}", status_code=204)
def trash_notebook(notebook_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    nb = _get_notebook_or_404(db, notebook_id, user)
    nb.is_trashed = True
    nb.trashed_at = datetime.now(timezone.utc)
    db.commit()


def _sync_wiki_links(db: Session, chapter: Chapter) -> None:
    """Re-derive this chapter's outgoing links from its current content."""
    db.query(ChapterLink).filter(ChapterLink.from_chapter_id == chapter.id).delete()
    titles = extract_wiki_links(chapter.content)
    if not titles:
        return
    targets = (
        db.query(Chapter)
        .filter(Chapter.title.in_(titles), Chapter.is_trashed.is_(False))
        .all()
    )
    for target in targets:
        if target.id != chapter.id:
            db.add(ChapterLink(from_chapter_id=chapter.id, to_chapter_id=target.id))


@router.get("/{notebook_id}/chapters", response_model=list[ChapterOut])
def list_chapters(
    notebook_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _get_notebook_or_404(db, notebook_id, user)
    return (
        db.query(Chapter)
        .filter(Chapter.notebook_id == notebook_id, Chapter.is_trashed.is_(False))
        .order_by(Chapter.pinned.desc(), Chapter.updated_at.desc())
        .all()
    )


@router.post("/{notebook_id}/chapters", response_model=ChapterOut, status_code=201)
def create_chapter(
    notebook_id: str,
    payload: ChapterCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_notebook_or_404(db, notebook_id, user)
    ch = Chapter(notebook_id=notebook_id, title=payload.title, content=payload.content)
    db.add(ch)
    db.commit()
    db.refresh(ch)
    _sync_wiki_links(db, ch)
    db.commit()
    return ch


@router.get("/chapters/recent", response_model=list[ChapterOut])
def list_recent_chapters(
    limit: int = 10, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Most recently updated chapters across all of the user's notebooks (Dashboard widget)."""
    return (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_trashed.is_(False))
        .order_by(Chapter.updated_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/chapters/{chapter_id}", response_model=ChapterOut)
def get_chapter(chapter_id: str, db: Session = Depends(get_db)):
    return _get_chapter_or_404(db, chapter_id)


@router.patch("/chapters/{chapter_id}", response_model=ChapterOut)
def update_chapter(chapter_id: str, payload: ChapterUpdate, db: Session = Depends(get_db)):
    ch = _get_chapter_or_404(db, chapter_id)
    data = payload.model_dump(exclude_unset=True)

    if "content" in data and data["content"] != ch.content:
        db.add(ChapterVersion(chapter_id=ch.id, content_snapshot=ch.content, version_number=ch.version))
        ch.version += 1

    for field, value in data.items():
        setattr(ch, field, value)

    db.commit()
    db.refresh(ch)

    if "content" in data:
        _sync_wiki_links(db, ch)
        db.commit()

    return ch


@router.delete("/chapters/{chapter_id}", status_code=204)
def trash_chapter(chapter_id: str, db: Session = Depends(get_db)):
    ch = _get_chapter_or_404(db, chapter_id)
    ch.is_trashed = True
    ch.trashed_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/chapters/{chapter_id}/backlinks", response_model=list[BacklinkOut])
def get_backlinks(chapter_id: str, db: Session = Depends(get_db)):
    """Chapters that link TO this chapter (the 'Referenced by' panel)."""
    _get_chapter_or_404(db, chapter_id)
    return (
        db.query(Chapter)
        .join(ChapterLink, ChapterLink.from_chapter_id == Chapter.id)
        .filter(ChapterLink.to_chapter_id == chapter_id, Chapter.is_trashed.is_(False))
        .all()
    )
