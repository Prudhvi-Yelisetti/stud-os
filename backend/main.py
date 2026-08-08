from dotenv import load_dotenv

load_dotenv()  # must run before any AI provider reads its API key from the env

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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


# Serving the built frontend from this same process is the packaged-app
# story (see packaging/appimage/) -- normal `npm run dev` usage never sets
# FRONTEND_DIST, so this whole block is a no-op for everyday development.
# Because the frontend already calls relative "/api/..." paths (see
# vite.config.ts's dev proxy), serving both from one origin needs zero
# per-build URL baking, unlike a split frontend/backend-process setup.
#
# Registered last on purpose: FastAPI/Starlette match routes in
# registration order, so every /api/* router above still wins over this
# catch-all for the paths it actually owns.
_frontend_dist = os.getenv("FRONTEND_DIST")
if _frontend_dist and (dist_path := Path(_frontend_dist)).is_dir():
    assets_dir = dist_path / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        # A real built file (favicon, manifest, etc.) wins if it exists;
        # everything else -- including client-side routes like /notes or
        # /tasks that don't correspond to a file on disk -- falls back to
        # index.html so React Router can handle it browser-side.
        candidate = dist_path / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist_path / "index.html")
