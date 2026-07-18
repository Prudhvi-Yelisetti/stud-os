import os
from pathlib import Path
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Anchor the default sqlite path to backend/ regardless of the process's
# CWD -- a relative "sqlite:///./stud_os.db" silently lands wherever the
# command happened to be run from, which caused dev DB files to scatter
# across the repo root during rebuild testing. Always resolve explicitly.
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "stud_os.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
