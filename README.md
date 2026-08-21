# Stud-OS

Personal knowledge, productivity, and AI operating system. See
`HANDOFF.md` for current status and session history.

## Status

All of V1 from the vision doc is built, tested, and in daily-usable
shape, plus a growing set of Obsidian-parity features added since (see
`HANDOFF.md` sessions 22 onward for the running list of what's still
missing toward full parity):

- **Notes** — notebooks/chapters, `[[wiki-links]]` with live autocomplete,
  backlinks, full markdown rendering (via `marked`), chapter version
  history (browse + non-destructive restore), attachments, export
  (chapter → `.md`/`.zip`, notebook → `.zip` of all chapters)
- **Tags & properties** — inline `#tags` and YAML frontmatter properties
  on notes and journal entries (frontmatter lives in the content itself,
  same philosophy as Obsidian's plain-file model), a Tags page (cloud of
  all tags with counts, click through to a filtered list), and an
  editable Properties panel
- **Templates & daily notes** — mark any chapter as a reusable template
  (with `{{date}}`/`{{time}}` interpolation) or as the one daily-note
  template, plus a one-click "Today" button that gets or creates the
  day's note
- **Embeds/transclusion** — `![[Note Title]]` expands another note's
  content inline wherever it's rendered, recursively, with a depth cap
  to survive circular embeds
- **Live-preview editor** — a CodeMirror-based editor (Notes and
  Journal) that hides markdown marks (`**`, `#`, `` ` ``) on every line
  except the one you're editing, so the page reads close to its
  rendered form while staying plain text underneath; wiki-links, tags,
  and embeds render as clickable colored pills with Ctrl/Cmd+click
  navigation
- **Canvas** — a freeform visual board (built on React Flow): text
  cards and note-reference cards connected by edges, autosaved
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
    internet connection required. Add and verify keys, pick a default
    provider, and curate which models to use — all from Settings. See
    "AI features" below.

**Not built, deliberately deferred:** real auth — it's a single hardcoded
local user, fine for personal use, would need work before ever being
multi-user or internet-facing. The source is published for transparency
and so anyone can self-host it, so this is a known, flagged limitation
rather than an oversight.

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
on first launch, outside the (read-only) AppImage itself. Every launch
also runs any pending database migrations against it automatically
(harmless no-op if already current), so updating to a newer AppImage
build never leaves an existing install's data on an outdated schema.

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

The easiest way to add a key: open **Settings** in the app, click
**"+ Add API key"**, pick a provider and paste its key, then hit
**Connect** — it's tested against the real provider before being saved
(a bad key is rejected with the actual reason, never silently stored),
writes straight into your `.env` file (never into the database), and
takes effect immediately, no restart. Editing `.env` by hand still
works too, if you prefer:
```bash
cp .env.example .env
# fill in whichever provider(s) you want, e.g. ANTHROPIC_API_KEY=...
```

Then, in **Settings**, set one connected provider as your **default** —
every chat-based feature uses that default automatically. Any feature
can still be pointed at a different connected provider individually if
you want one thing (say, a paid model for study quizzes) to differ from
the rest. Any connected provider also has a **"Test connection"**
button to re-check it's still reachable at any time, and a **"Models"**
toggle to fetch that provider's live model catalog and add specific
models to use — the first model added becomes that provider's default
automatically, and the Ask page lets you pick which added model to use
per chat. Supported providers: Anthropic, Gemini, OpenAI, OpenRouter,
Groq, NVIDIA NIM, DeepSeek, Mistral AI, xAI (Grok), Perplexity (Sonar),
Ollama, LM Studio. See `.env.example` for the exact env var names and
optional model overrides, if you'd rather edit `.env` directly than use
Settings.

Ollama and LM Studio run entirely on your own machine — no API key,
no per-request cost, no data leaving your computer. Install either one,
load/pull a model, start its local server, and it shows up in Settings
with no `.env` changes needed (override the model or base URL there only
if you're not using the defaults — see `.env.example`).

## License

Source-available, not open source: you're free to use, run, and
self-host this software for any purpose, but copying, redistributing,
publishing, or creating derivative works from the source code requires
prior written permission from the copyright holder. See `LICENSE` for
the exact terms.
