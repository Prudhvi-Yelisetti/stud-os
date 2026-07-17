from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import models  # noqa: F401 -- registers models on Base.metadata
from backend.database.session import SessionLocal
from backend.gamification.badges import ensure_badges_seeded
from backend.routers import notes, tasks, journal, gamification, projects, search, graph

app = FastAPI(title="Stud-OS API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router)
app.include_router(tasks.router)
app.include_router(journal.router)
app.include_router(gamification.router)
app.include_router(projects.router)
app.include_router(search.router)
app.include_router(graph.router)


@app.on_event("startup")
def on_startup() -> None:
    # Data seeding only -- schema comes from Alembic migrations, never from
    # app code. See REBUILD_PLAN.md section 7 for why that boundary matters.
    db = SessionLocal()
    try:
        ensure_badges_seeded(db)
    finally:
        db.close()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
