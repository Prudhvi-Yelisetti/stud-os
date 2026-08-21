from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.canvas import Canvas
from backend.database.models.user import User
from backend.dependencies import get_current_user
from backend.schemas.canvas import CanvasCreate, CanvasUpdate, CanvasOut

router = APIRouter(prefix="/api/canvases", tags=["canvas"])


def _get_canvas_or_404(db: Session, canvas_id: str, user: User) -> Canvas:
    canvas = (
        db.query(Canvas)
        .filter(Canvas.id == canvas_id, Canvas.user_id == user.id, Canvas.is_trashed.is_(False))
        .first()
    )
    if canvas is None:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas


@router.get("", response_model=list[CanvasOut])
def list_canvases(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Canvas)
        .filter(Canvas.user_id == user.id, Canvas.is_trashed.is_(False))
        .order_by(Canvas.updated_at.desc())
        .all()
    )


@router.post("", response_model=CanvasOut, status_code=201)
def create_canvas(payload: CanvasCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    canvas = Canvas(user_id=user.id, title=payload.title, data="{}")
    db.add(canvas)
    db.commit()
    db.refresh(canvas)
    return canvas


@router.get("/{canvas_id}", response_model=CanvasOut)
def get_canvas(canvas_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_canvas_or_404(db, canvas_id, user)


@router.patch("/{canvas_id}", response_model=CanvasOut)
def update_canvas(
    canvas_id: str, payload: CanvasUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    canvas = _get_canvas_or_404(db, canvas_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(canvas, field, value)
    db.commit()
    db.refresh(canvas)
    return canvas


@router.delete("/{canvas_id}", status_code=204)
def trash_canvas(canvas_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    canvas = _get_canvas_or_404(db, canvas_id, user)
    canvas.is_trashed = True
    canvas.trashed_at = datetime.now(timezone.utc)
    db.commit()
