"""
Shared pytest fixtures. Every test gets a fresh, isolated SQLite file
(never the dev database at backend/stud_os.db) via a dependency override
on get_db -- this is what makes the test suite safe to run against a
live dev server without stepping on its data.
"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base
from backend.database import models  # noqa: F401 -- registers all models
from backend.database.session import get_db
from backend.main import app


@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()
    os.close(db_fd)
    os.remove(db_path)
