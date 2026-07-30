# Stud-OS

Personal knowledge, productivity, and AI operating system. See
`HANDOFF.md` for current status and session history.

## Status

All of V1 from the vision doc is built, tested, and in daily-usable shape:

- **Notes** — notebooks/chapters, `[[wiki-links]]` with live autocomplete,
  backlinks, full markdown rendering (via `marked`), chapter version
  history (browse + non-destructive restore), attachments, export
  (chapter → `.md`/`.zip`, notebook → `.zip` of all chapters)
- **Tasks** — Kanban, recurring scheduling (auto-spawns next occurrence),
  subtasks, overdue penalties (actually wired up, not dead code)
- **Gamification** — XP/levels/streaks/badges, tied to task completion
- **Journal** — entries with mood, wiki-link rendering, mood heatmap
- **Projects** — with description, linked tasks
- **Search** — global keyword search, results are clickable/navigable
- **Knowledge Graph** — React Flow visualization across all entity types
- **Dashboard** — widgets + onboarding banner for empty workspaces
- **Timeline**, **Trash** (restore + permanent delete)
- Full edit/delete everywhere, modal-based create/edit (title+description)
- Mobile-responsive (hamburger drawer, drill-down navigation, horizontal
  Kanban scroll) down to ~375px
- CI on GitHub Actions (pytest + frontend build, runs on every push)

**Not built, deliberately deferred:** the V2 AI layer (suggestions,
semantic search, study coach) — waiting on an actual architecture
conversation (local LLM vs. API-based, cost, which model) rather than
being built ad hoc. Real auth is also not built — it's a single
hardcoded local user, fine for personal use, would need work before
ever being multi-user or internet-facing.

See `HANDOFF.md` for a full session-by-session history and current
state, and `REBUILD_PLAN.md` for the original architecture/data-model
plan (now a historical record — see its closing note).

## Running locally

### Backend (FastAPI)
```bash
cd backend
../.venv/bin/python -m alembic -c alembic.ini upgrade head   # from repo root instead: alembic -c backend/alembic.ini upgrade head
../.venv/bin/python -m uvicorn backend.main:app --reload --port 8420
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
backend on port 8420. (Not 8000 — that's used by other projects on this
machine; see vite.config.ts if you ever need to change it again.)

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
