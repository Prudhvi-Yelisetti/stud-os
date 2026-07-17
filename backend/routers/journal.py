from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.journal import JournalEntry
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.journal import JournalEntryCreate, JournalEntryUpdate, JournalEntryOut

router = APIRouter(prefix="/api/journal", tags=["journal"])


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
    return entry


@router.get("/{entry_id}", response_model=JournalEntryOut)
def get_entry(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_entry_or_404(db, entry_id, user)


@router.patch("/{entry_id}", response_model=JournalEntryOut)
def update_entry(
    entry_id: str,
    payload: JournalEntryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    entry = _get_entry_or_404(db, entry_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def trash_entry(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    entry = _get_entry_or_404(db, entry_id, user)
    entry.is_trashed = True
    entry.trashed_at = datetime.now(timezone.utc)
    db.commit()
