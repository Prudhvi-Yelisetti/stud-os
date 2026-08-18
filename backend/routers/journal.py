from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.journal import JournalEntry
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.journal import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryOut, JournalEntryPropertiesUpdate,
)
from backend.utils.frontmatter import parse_frontmatter, serialize_frontmatter
from backend.ai.indexing import reindex
from backend.tag_indexing import reindex_tags

router = APIRouter(prefix="/api/journal", tags=["journal"])


def _reindex_entry(db: Session, entry: JournalEntry) -> None:
    reindex(
        db,
        user_id=entry.user_id,
        parent_type="journal",
        parent_id=entry.id,
        parent_title=entry.title,
        content=entry.content,
    )


def _get_entry_or_404(db: Session, entry_id: str, user: User) -> JournalEntry:
    entry = (
        db.query(JournalEntry)
        .filter(JournalEntry.id == entry_id, JournalEntry.user_id == user.id, JournalEntry.is_trashed.is_(False))
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.get("", response_model=list[JournalEntryOut])
def list_entries(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user.id, JournalEntry.is_trashed.is_(False))
        .order_by(JournalEntry.entry_date.desc())
        .all()
    )


@router.post("", response_model=JournalEntryOut, status_code=201)
def create_entry(
    payload: JournalEntryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    entry = JournalEntry(user_id=user.id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    _reindex_entry(db, entry)
    reindex_tags(db, taggable_type="journal", taggable_id=entry.id, content=entry.content)
    db.commit()
    return entry


@router.patch("/{entry_id}", response_model=JournalEntryOut)
def update_entry(
    entry_id: str,
    payload: JournalEntryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = _get_entry_or_404(db, entry_id, user)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    if "content" in data or "title" in data:
        _reindex_entry(db, entry)
    if "content" in data:
        reindex_tags(db, taggable_type="journal", taggable_id=entry.id, content=entry.content)
    if "content" in data or "title" in data:
        db.commit()
    return entry


@router.patch("/{entry_id}/properties", response_model=JournalEntryOut)
def update_entry_properties(
    entry_id: str,
    payload: JournalEntryPropertiesUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Same shape as ChapterOut's properties endpoint -- rewrites the
    frontmatter block in content, keeps body untouched."""
    entry = _get_entry_or_404(db, entry_id, user)
    _, body = parse_frontmatter(entry.content)
    new_content = serialize_frontmatter(payload.properties, body)

    if new_content != entry.content:
        entry.content = new_content
        db.commit()
        db.refresh(entry)
        _reindex_entry(db, entry)
        reindex_tags(db, taggable_type="journal", taggable_id=entry.id, content=entry.content)
        db.commit()

    return entry


@router.delete("/{entry_id}", status_code=204)
def trash_entry(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entry = _get_entry_or_404(db, entry_id, user)
    entry.is_trashed = True
    entry.trashed_at = datetime.now(timezone.utc)
    db.commit()
