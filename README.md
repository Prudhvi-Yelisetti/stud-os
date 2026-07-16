# Stud-OS

Personal knowledge, productivity, and AI operating system. See
`REBUILD_PLAN.md` for the full architecture, data model, and roadmap.

## Status

**Phase 1 (Core knowledge layer) — done:** Notebooks, Chapters,
`[[wiki-links]]`, backlinks, chapter version history.

**Next up:** Phase 2 — Tasks (Kanban + recurring scheduling) and the
gamification engine (XP/levels/badges/streaks/penalties).

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
