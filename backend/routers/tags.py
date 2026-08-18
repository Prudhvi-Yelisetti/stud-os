from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.tags import Tag, TagLink
from backend.database.models.notes import Chapter, Notebook
from backend.database.models.journal import JournalEntry
from backend.database.models.user import User
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/tags", tags=["tags"])


class TagCount(BaseModel):
    name: str
    count: int


class TaggedItem(BaseModel):
    type: str  # "chapter" | "journal"
    id: str
    title: str
    notebook_id: str | None = None


def _owned_taggable_ids(db: Session, user: User) -> set[str]:
    """Chapter and JournalEntry ids the user actually owns and hasn't
    trashed -- Tag/TagLink have no user_id of their own (global rows,
    same reasoning as Chunk/Attachment being polymorphic), so every
    lookup here scopes through this instead."""
    chapter_ids = {
        row[0]
        for row in db.query(Chapter.id)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_trashed.is_(False))
        .all()
    }
    journal_ids = {
        row[0]
        for row in db.query(JournalEntry.id)
        .filter(JournalEntry.user_id == user.id, JournalEntry.is_trashed.is_(False))
        .all()
    }
    return chapter_ids | journal_ids


@router.get("", response_model=list[TagCount])
def list_tags(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Every tag currently in use, with how many notes/journal entries
    carry it. Powers the Tags page (a tag cloud/list, click-through to
    filter) -- the closest equivalent to Obsidian's tag pane."""
    owned_ids = _owned_taggable_ids(db, user)
    if not owned_ids:
        return []
    rows = (
        db.query(Tag.name, func.count(TagLink.id))
        .join(TagLink, TagLink.tag_id == Tag.id)
        .filter(TagLink.taggable_id.in_(owned_ids))
        .group_by(Tag.name)
        .order_by(Tag.name)
        .all()
    )
    return [TagCount(name=name, count=count) for name, count in rows]


@router.get("/{tag_name}", response_model=list[TaggedItem])
def get_tagged_items(tag_name: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Chapters and journal entries carrying this tag."""
    tag = db.query(Tag).filter(Tag.name == tag_name.strip().lower()).first()
    if tag is None:
        return []

    owned_ids = _owned_taggable_ids(db, user)
    links = db.query(TagLink).filter(TagLink.tag_id == tag.id, TagLink.taggable_id.in_(owned_ids)).all()

    chapter_ids = [link.taggable_id for link in links if link.taggable_type == "chapter"]
    journal_ids = [link.taggable_id for link in links if link.taggable_type == "journal"]

    items: list[TaggedItem] = []
    if chapter_ids:
        chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
        items += [TaggedItem(type="chapter", id=c.id, title=c.title, notebook_id=c.notebook_id) for c in chapters]
    if journal_ids:
        entries = db.query(JournalEntry).filter(JournalEntry.id.in_(journal_ids)).all()
        items += [TaggedItem(type="journal", id=e.id, title=e.title) for e in entries]

    return items
