"""
Regression test for the get_current_user race condition: two requests
racing to create the default user on a fresh DB used to 500 on whichever
one lost the INSERT race. Simulated directly with two DB sessions against
the same underlying file, since a true HTTP-level race is non-deterministic.
"""
import tempfile
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base
from backend.database import models  # noqa: F401
from backend.dependencies import get_current_user, DEFAULT_USER_EMAIL
from backend.database.models.user import User


def test_concurrent_default_user_creation_does_not_500():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    session_a = SessionLocal()
    session_b = SessionLocal()
    try:
        # Both sessions see an empty users table -- simulates two parallel
        # requests hitting get_current_user before either has committed.
        user_a = get_current_user(db=session_a)
        user_b = get_current_user(db=session_b)

        assert user_a.email == DEFAULT_USER_EMAIL
        assert user_b.email == DEFAULT_USER_EMAIL
        assert user_a.id == user_b.id  # both resolved to the SAME row, not two

        # Exactly one row should exist, not two.
        count = session_a.query(User).filter(User.email == DEFAULT_USER_EMAIL).count()
        assert count == 1
    finally:
        session_a.close()
        session_b.close()
        engine.dispose()
        os.close(db_fd)
        os.remove(db_path)
