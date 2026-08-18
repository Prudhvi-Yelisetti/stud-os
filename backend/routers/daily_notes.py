"""
Get-or-create today's daily note. Lives in an auto-created "Daily Notes"
notebook, one chapter per calendar date (title = YYYY-MM-DD), optionally
seeded from whichever chapter has is_daily_template=True (see
routers/notes.py's single-daily-template invariant in update_chapter).
"""
from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.notes import Notebook, Chapter
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.notes import ChapterOut
from backend.routers.notes import create_chapter_record
from backend.utils.templates import interpolate

router = APIRouter(prefix="/api/daily-notes", tags=["daily-notes"])

DAILY_NOTEBOOK_TITLE = "Daily Notes"


@router.post("/today", response_model=ChapterOut)
def get_or_create_today(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    notebook = (
        db.query(Notebook)
        .filter(
            Notebook.user_id == user.id,
            Notebook.title == DAILY_NOTEBOOK_TITLE,
            Notebook.is_trashed.is_(False),
        )
        .first()
    )
    if notebook is None:
        notebook = Notebook(
            user_id=user.id, title=DAILY_NOTEBOOK_TITLE, description="Auto-created for daily notes."
        )
        db.add(notebook)
        db.commit()
        db.refresh(notebook)

    today_title = date.today().isoformat()
    existing = (
        db.query(Chapter)
        .filter(Chapter.notebook_id == notebook.id, Chapter.title == today_title, Chapter.is_trashed.is_(False))
        .first()
    )
    if existing is not None:
        return existing

    template = (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_daily_template.is_(True), Chapter.is_trashed.is_(False))
        .first()
    )
    content = interpolate(template.content, datetime.now()) if template else ""

    return create_chapter_record(db, notebook_id=notebook.id, title=today_title, content=content)
