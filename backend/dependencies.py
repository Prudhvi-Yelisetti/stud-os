"""
Stud-OS is a personal, single-user system (per the vision doc). Rather than
build a full auth flow before there's anything to protect, this dependency
gets-or-creates a single default user and every router depends on it. Swap
this for real auth later without touching the routers' signatures.
"""
from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.user import User

DEFAULT_USER_EMAIL = "me@stud-os.local"


def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.email == DEFAULT_USER_EMAIL).first()
    if user is not None:
        return user

    # Several requests can race to create the default user on first-ever
    # load (a fresh DB, several API calls firing in parallel) -- only one
    # INSERT wins; the rest hit a UNIQUE violation on email. Rather than
    # 500 on the losers, just re-fetch the row the winner created.
    try:
        user = User(email=DEFAULT_USER_EMAIL, name="Stud-OS User")
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        return db.query(User).filter(User.email == DEFAULT_USER_EMAIL).first()
