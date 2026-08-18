import io
import os
import re
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.notes import Notebook, Chapter, ChapterLink, ChapterVersion
from backend.database.models.attachments import Attachment
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.notes import (
    NotebookCreate, NotebookUpdate, NotebookOut,
    ChapterCreate, ChapterUpdate, ChapterOut, ChapterPropertiesUpdate,
    BacklinkOut, ChapterTitleMatch, ChapterVersionOut,
)
from backend.utils.wiki_parser import extract_wiki_links
from backend.utils.frontmatter import parse_frontmatter, serialize_frontmatter
from backend.utils.templates import interpolate
from backend.ai.indexing import reindex
from backend.tag_indexing import reindex_tags

router = APIRouter(prefix="/api/notebooks", tags=["notes"])


def _safe_filename(title: str) -> str:
    cleaned = re.sub(r'[^\w\- ]', '_', title).strip()
    return cleaned or "untitled"


def _chapter_markdown(chapter: Chapter) -> str:
    return f"# {chapter.title}\n\n{chapter.content}"


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


@router.get("/{notebook_id}/export")
def export_notebook(notebook_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Zip of every chapter as its own .md file, with each chapter's
    attachments (if any) alongside it under attachments/<chapter title>/."""
    nb = _get_notebook_or_404(db, notebook_id, user)
    chapters = (
        db.query(Chapter)
        .filter(Chapter.notebook_id == notebook_id, Chapter.is_trashed.is_(False))
        .all()
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for ch in chapters:
            base = _safe_filename(ch.title)
            zf.writestr(f"{base}.md", _chapter_markdown(ch))
            attachments = (
                db.query(Attachment)
                .filter(Attachment.owner_type == "chapter", Attachment.owner_id == ch.id)
                .all()
            )
            for att in attachments:
                if os.path.exists(att.stored_path):
                    zf.write(att.stored_path, arcname=f"attachments/{base}/{att.filename}")
    buf.seek(0)

    filename = f"{_safe_filename(nb.title)}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _reindex_chapter(db: Session, chapter: Chapter) -> None:
    """Re-embed this chapter's content for semantic search. Chapter has no
    user_id of its own (see ChapterLink comment pattern) -- scope through
    its notebook, same as everywhere else chapter ownership is needed."""
    notebook = db.query(Notebook).filter(Notebook.id == chapter.notebook_id).first()
    if notebook is None:
        return
    reindex(
        db,
        user_id=notebook.user_id,
        parent_type="chapter",
        parent_id=chapter.id,
        parent_title=chapter.title,
        content=chapter.content,
    )


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


def create_chapter_record(db: Session, *, notebook_id: str, title: str, content: str = "") -> Chapter:
    """Shared chapter-creation path: insert, sync wiki-links, reindex for
    search and tags. Used by the plain create_chapter endpoint below and
    by anything else that creates a chapter programmatically (templates,
    daily notes) so none of those paths can drift out of sync with it."""
    ch = Chapter(notebook_id=notebook_id, title=title, content=content)
    db.add(ch)
    db.commit()
    db.refresh(ch)
    _sync_wiki_links(db, ch)
    _reindex_chapter(db, ch)
    reindex_tags(db, taggable_type="chapter", taggable_id=ch.id, content=ch.content)
    db.commit()
    return ch


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
    return create_chapter_record(db, notebook_id=notebook_id, title=payload.title, content=payload.content)


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


@router.get("/chapters/search", response_model=list[ChapterTitleMatch])
def search_chapter_titles(
    q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Title-only lookup across all of the user's notebooks. Powers wiki-link
    autocomplete while typing [[ and exact-match resolution when a link
    is clicked in preview mode.
    """
    if not q or not q.strip():
        return []
    like = f"%{q.strip()}%"
    return (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_trashed.is_(False), Chapter.title.ilike(like))
        .order_by(Chapter.title)
        .limit(8)
        .all()
    )


@router.get("/chapters/templates", response_model=list[ChapterOut])
def list_templates(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Chapters marked is_template=True, across all notebooks -- powers
    the "New from template" picker. Must be declared before the
    /chapters/{chapter_id} route below or FastAPI would match "templates"
    as a chapter_id (same reasoning as /chapters/recent and /search)."""
    return (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_trashed.is_(False), Chapter.is_template.is_(True))
        .order_by(Chapter.title)
        .all()
    )


@router.post("/{notebook_id}/chapters/from-template/{template_id}", response_model=ChapterOut, status_code=201)
def create_chapter_from_template(
    notebook_id: str,
    template_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_notebook_or_404(db, notebook_id, user)
    template = _get_chapter_or_404(db, template_id)
    if not template.is_template:
        raise HTTPException(status_code=400, detail="Chapter is not marked as a template")

    now = datetime.now()
    title = interpolate(template.title, now).strip() or "Untitled"
    content = interpolate(template.content, now)
    return create_chapter_record(db, notebook_id=notebook_id, title=title, content=content)


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

    # At most one chapter is the daily template at a time -- unset any
    # other one that currently holds it (mirrors the "exactly one default
    # model" invariant from the AI-models settings page).
    if data.get("is_daily_template") is True:
        db.query(Chapter).filter(Chapter.id != ch.id, Chapter.is_daily_template.is_(True)).update(
            {"is_daily_template": False}
        )

    db.commit()
    db.refresh(ch)

    if "content" in data:
        _sync_wiki_links(db, ch)
        reindex_tags(db, taggable_type="chapter", taggable_id=ch.id, content=ch.content)

    if "content" in data or "title" in data:
        _reindex_chapter(db, ch)
        db.commit()

    return ch


@router.patch("/chapters/{chapter_id}/properties", response_model=ChapterOut)
def update_chapter_properties(chapter_id: str, payload: ChapterPropertiesUpdate, db: Session = Depends(get_db)):
    """Rewrites the chapter's frontmatter block to match `properties`,
    keeping the body untouched, and saves it as a normal content edit
    (version-snapshotted, wiki-links and tags re-synced) -- properties
    aren't a separate store, they live in content like everything else."""
    ch = _get_chapter_or_404(db, chapter_id)
    _, body = parse_frontmatter(ch.content)
    new_content = serialize_frontmatter(payload.properties, body)

    if new_content != ch.content:
        db.add(ChapterVersion(chapter_id=ch.id, content_snapshot=ch.content, version_number=ch.version))
        ch.version += 1
        ch.content = new_content
        db.commit()
        db.refresh(ch)
        _sync_wiki_links(db, ch)
        _reindex_chapter(db, ch)
        reindex_tags(db, taggable_type="chapter", taggable_id=ch.id, content=ch.content)
        db.commit()

    return ch


@router.delete("/chapters/{chapter_id}", status_code=204)
def trash_chapter(chapter_id: str, db: Session = Depends(get_db)):
    ch = _get_chapter_or_404(db, chapter_id)
    ch.is_trashed = True
    ch.trashed_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/chapters/{chapter_id}/export")
def export_chapter(chapter_id: str, db: Session = Depends(get_db)):
    """Plain .md download, or a zip alongside its attachments if it has any."""
    ch = _get_chapter_or_404(db, chapter_id)
    base = _safe_filename(ch.title)
    attachments = (
        db.query(Attachment)
        .filter(Attachment.owner_type == "chapter", Attachment.owner_id == ch.id)
        .all()
    )

    if not attachments:
        return Response(
            content=_chapter_markdown(ch),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{base}.md"'},
        )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{base}.md", _chapter_markdown(ch))
        for att in attachments:
            if os.path.exists(att.stored_path):
                zf.write(att.stored_path, arcname=f"attachments/{att.filename}")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{base}.zip"'},
    )


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


@router.get("/chapters/{chapter_id}/versions", response_model=list[ChapterVersionOut])
def list_chapter_versions(chapter_id: str, db: Session = Depends(get_db)):
    """Past snapshots, newest first. The current content is NOT included
    here -- it lives on the chapter itself, this is history only."""
    _get_chapter_or_404(db, chapter_id)
    return (
        db.query(ChapterVersion)
        .filter(ChapterVersion.chapter_id == chapter_id)
        .order_by(ChapterVersion.version_number.desc())
        .all()
    )


@router.post("/chapters/{chapter_id}/versions/{version_id}/restore", response_model=ChapterOut)
def restore_chapter_version(chapter_id: str, version_id: str, db: Session = Depends(get_db)):
    """
    Restores a past snapshot as the chapter's current content. The content
    being replaced is itself snapshotted first, so restoring never loses
    data -- it's just another entry in the history, not a destructive undo.
    """
    ch = _get_chapter_or_404(db, chapter_id)
    target_version = (
        db.query(ChapterVersion)
        .filter(ChapterVersion.id == version_id, ChapterVersion.chapter_id == chapter_id)
        .first()
    )
    if target_version is None:
        raise HTTPException(status_code=404, detail="Version not found")

    db.add(ChapterVersion(chapter_id=ch.id, content_snapshot=ch.content, version_number=ch.version))
    ch.version += 1
    ch.content = target_version.content_snapshot
    db.commit()
    db.refresh(ch)

    _sync_wiki_links(db, ch)
    _reindex_chapter(db, ch)
    reindex_tags(db, taggable_type="chapter", taggable_id=ch.id, content=ch.content)
    db.commit()
    return ch
