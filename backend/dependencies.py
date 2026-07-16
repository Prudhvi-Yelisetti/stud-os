"""
Stud-OS is a personal, single-user system (per the vision doc). Rather than
build a full auth flow before there's anything to protect, this dependency
gets-or-creates a single default user and every router depends on it. Swap
this for real auth later without touching the routers' signatures.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.user import User

DEFAULT_USER_EMAIL = "me@stud-os.local"


def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.email == DEFAULT_USER_EMAIL).first()
    if user is None:
        user = User(email=DEFAULT_USER_EMAIL, name="Stud-OS User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
