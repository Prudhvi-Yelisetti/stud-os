from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.base import Base
from backend.database.session import engine
from backend.database import models  # noqa: F401 -- registers models on Base.metadata
from backend.routers import notes

app = FastAPI(title="Stud-OS API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router)


@app.on_event("startup")
def on_startup() -> None:
    # Dev convenience only -- Alembic migrations are the source of truth.
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
