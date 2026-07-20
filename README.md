# Stud-OS

Personal knowledge, productivity, and AI operating system. See
`REBUILD_PLAN.md` for the full architecture, data model, and roadmap.

## Status

Nearly all of V1 from the vision doc is built and working: Notes
(notebooks/chapters/`[[wiki-links]]`/backlinks/version history), Tasks
(Kanban + recurring scheduling), Gamification (XP/levels/streaks/badges/
penalties), Journal, Projects/Subtasks, global keyword Search, the
Knowledge Graph (React Flow), a 5-widget Dashboard, Timeline, and file
Attachments.

**Not yet built:** AI layer (V2 in the vision doc — suggestions, semantic
search, study coach). Intentionally deferred until there's enough real
content in the graph for it to be worth building against.

See `REBUILD_PLAN.md` for the full data model and phase-by-phase history.

## Running locally

### Backend (FastAPI)
```bash
cd backend
../.venv/bin/python -m alembic -c alembic.ini upgrade head   # from repo root instead: alembic -c backend/alembic.ini upgrade head
../.venv/bin/python -m uvicorn backend.main:app --reload --port 8000
```
Run alembic commands from the **repo root**, not `backend/`:
```bash
.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
```

### Frontend (Vite + React)
```bash
cd frontend
npm install   # first time only
npm run dev
```
Visit http://localhost:5173 — the dev server proxies `/api` to the
backend on port 8000.

## Testing

Two layers, both run from the repo root:

**Unit + integration (pytest)** — isolated, never touches the dev
database, safe to run anytime including against a live dev server:
```bash
uv pip install --python .venv/bin/python -r backend/requirements-dev.txt   # first time only
.venv/bin/python -m pytest
```

**End-to-end smoke test** — real HTTP calls against a *running* backend,
exercises the full feature surface in one pass. Start the backend first:
```bash
.venv/bin/python backend/qa_check.py
```
