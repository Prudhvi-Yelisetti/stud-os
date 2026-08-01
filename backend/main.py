from dotenv import load_dotenv

load_dotenv()  # must run before any AI provider reads its API key from the env

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import models  # noqa: F401 -- registers models on Base.metadata
from backend.routers import notes, tasks, journal, gamification, projects, search, graph, attachments, trash, ai

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
app.include_router(attachments.router)
app.include_router(trash.router)
app.include_router(ai.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
