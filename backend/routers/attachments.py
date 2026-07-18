import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.attachments import Attachment
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.attachments import AttachmentOut

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_OWNER_TYPES = {"chapter", "project", "journal"}


@router.get("", response_model=list[AttachmentOut])
def list_attachments(
    owner_type: str, owner_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return (
        db.query(Attachment)
        .filter(
            Attachment.user_id == user.id,
            Attachment.owner_type == owner_type,
            Attachment.owner_id == owner_id,
        )
        .order_by(Attachment.created_at.desc())
        .all()
    )


@router.post("", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    owner_type: str,
    owner_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if owner_type not in ALLOWED_OWNER_TYPES:
        raise HTTPException(status_code=400, detail=f"owner_type must be one of {ALLOWED_OWNER_TYPES}")

    contents = await file.read()
    stored_name = f"{uuid.uuid4()}_{file.filename}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(contents)

    attachment = Attachment(
        user_id=user.id,
        owner_type=owner_type,
        owner_id=owner_id,
        filename=file.filename or stored_name,
        stored_path=stored_path,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/{attachment_id}/download")
def download_attachment(attachment_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    att = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.user_id == user.id).first()
    if att is None or not os.path.exists(att.stored_path):
        raise HTTPException(status_code=404, detail="Attachment not found")
    return FileResponse(att.stored_path, filename=att.filename, media_type=att.mime_type)


@router.delete("/{attachment_id}", status_code=204)
def delete_attachment(attachment_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    att = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.user_id == user.id).first()
    if att is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if os.path.exists(att.stored_path):
        os.remove(att.stored_path)
    db.delete(att)
    db.commit()
