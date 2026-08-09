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
- **AI layer — fully built**, four phases, all reusing the same provider
  abstraction:
  - **Semantic search** — meaning-based search over notes/journal,
    always local (`all-MiniLM-L6-v2`), no API key or cost
  - **Task suggestions** — "what should I work on next," on the dashboard
  - **Study coach** — generates a quiz from any chapter's content
  - **Ask your notes** — multi-turn chat that answers using your own
    notes/journal as context, with sources shown and clickable
  - Bring your own API key for the chat-completion features (semantic
    search never needs one): Anthropic, Gemini, OpenAI, OpenRouter, Groq,
    NVIDIA NIM, DeepSeek, Mistral AI, xAI (Grok), or Perplexity (Sonar) —
    or run a model fully locally with Ollama or LM Studio, no key or
    internet connection required. Pick per-feature in Settings. See
    "AI features" below.

**Not built, deliberately deferred:** real auth — it's a single hardcoded
local user, fine for personal use, would need work before ever being
multi-user or internet-facing. The project is going open-source, so this
is a known, flagged limitation rather than an oversight.

See `HANDOFF.md` for a full session-by-session history and current
state, and `REBUILD_PLAN.md` for the original architecture/data-model
plan (now a historical record — see its closing note).

## Running locally

Run everything from the **repo root** — `backend` is imported as a
package (`from backend.database import ...`), so it needs to be on the
path from one level up, not run from inside `backend/`.

### Backend (FastAPI)
```bash
.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
.venv/bin/python -m uvicorn backend.main:app --reload --port 8420
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

## Packaged desktop app (Linux)

For everyday use without manually running `npm run dev` / `uvicorn`
every time, build a self-contained AppImage:
```bash
./packaging/appimage/build.sh
```
Produces `Stud-OS-x86_64.AppImage` in the repo root — one file, no
install step. Double-click it (or run it from a terminal) and it opens
your browser at the app; `Ctrl+C` in that terminal (or closing the
window it opened from) stops it.

What this bundles: backend + a self-contained Python venv + the built
frontend, all served from one FastAPI process on port 8420 — no
separate frontend dev server, no manual migrations. What it does *not*
bundle: any AI provider key, or Ollama/LM Studio themselves (see
"AI features" below) — those stay exactly as optional as they are in
dev, configured per-feature in Settings after first launch.

Your data lives in `~/.local/share/Stud-OS/stud_os.db`, untouched by
re-running the build or updating to a new AppImage — it's created once,
on first launch, outside the (read-only) AppImage itself.

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

## AI features

Semantic search works out of the box — it runs a small local embedding
model (`all-MiniLM-L6-v2`, downloads once from HuggingFace on first use),
no API key needed.

The rest (task suggestions, study coach, ask-your-notes) need a
configured provider — either an API key for a hosted service, or a local
model server (Ollama/LM Studio) with nothing to configure at all.

The easiest way to add a key: open **Settings** in the app and paste it
into the provider's key field there — it writes straight into your
`.env` file for you (never into the database) and takes effect
immediately, no restart. Editing `.env` by hand still works too, if you
prefer:
```bash
cp .env.example .env
# fill in whichever provider(s) you want, e.g. ANTHROPIC_API_KEY=...
```

Then, in **Settings**, connect a provider (paste its key, or nothing to
do for Ollama/LM Studio) and set one as your **default** — every
chat-based feature uses that default automatically. Any feature can
still be pointed at a different connected provider individually if you
want one thing (say, a paid model for study quizzes) to differ from the
rest. Supported: Anthropic, Gemini, OpenAI, OpenRouter, Groq, NVIDIA NIM,
DeepSeek, Mistral AI, xAI (Grok), Perplexity (Sonar), Ollama, LM Studio.
See `.env.example` for the exact env var names and optional model
overrides, if you'd rather edit `.env` directly than use Settings.

Ollama and LM Studio run entirely on your own machine — no API key,
no per-request cost, no data leaving your computer. Install either one,
load/pull a model, start its local server, and it shows up in Settings
with no `.env` changes needed (override the model or base URL there only
if you're not using the defaults — see `.env.example`).
