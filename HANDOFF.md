# Stud-OS — Handoff

Written to let a fresh chat pick up this project with zero lost context.
If you're a new Claude session reading this: read this whole file before
touching anything. It'll save you from re-deriving things the hard way.

---

## 1. What this is

Stud-OS is Prudhvi's personal "second brain" app — notes with wiki-links,
tasks with gamification, journal, projects, a knowledge graph, dashboard,
timeline. Single local user, no auth. FastAPI + SQLite backend, React +
Vite frontend. Repo: https://github.com/Prudhvi-Yelisetti/stud-os

**Current state: V1 is complete, tested, and genuinely usable daily.**
Not a prototype — every feature below was built, then verified with real
HTTP calls and/or a real browser (Playwright), not just "should work."
**Semantic search (AI layer, Phase 1) is also done** — see §3 and §7.

**Going open-source, not just personal use.** Decided in the AI-layer
conversation (§7) — this shapes design choices going forward: no
hardcoded secrets, provider abstraction so contributors/users bring
their own API keys, README should be written for someone else running
this, not just Prudhvi. Auth is *not* in scope yet (deliberately kept
single-user for now, see "What's NOT built").

---

## 2. How to run it

```bash
cd ~/Projects/stud-os

# backend
.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
.venv/bin/python -m uvicorn backend.main:app --reload --port 8420

# frontend (separate terminal)
cd frontend && npm run dev
```
Visit http://localhost:5173.

**Port 8420, not 8000.** Port 8000 belongs to a *different* project on
this machine (`~/Projects/Aether`) — never kill processes there, never
change Stud-OS back to 8000. If you see "address already in use" on 8000,
that's Aether, not us.

**Testing:**
```bash
.venv/bin/python -m pytest                # 66 tests, isolated temp DB, safe anytime
.venv/bin/python backend/qa_check.py       # needs a running backend; 24-check e2e smoke test
cd frontend && npm run build               # tsc + vite build, catches type errors too
```

**First run note:** semantic search needs `sentence-transformers` +
CPU-only `torch`. If reinstalling deps from scratch, install torch from
the CPU index *first* to avoid pulling ~2.5GB of unneeded CUDA packages:
```bash
uv pip install --python .venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python sentence-transformers
```
The embedding model (~80MB) downloads from HuggingFace on first use —
the first chapter/journal save or search after a fresh install takes a
few extra seconds while it downloads and loads; after that it's cached
and fast.

---

## 3. What's built (V1, complete)

- **Notes** — notebooks → chapters, `[[wiki-links]]` with live autocomplete
  while typing, backlinks ("referenced by"), full markdown rendering in
  Preview mode (headers/bold/code/lists via `marked`, not just wiki-links),
  chapter version history (browse + restore — restoring snapshots the
  *current* content first, so it's never destructive), attachments,
  export (chapter → `.md` or `.zip` w/ attachments, notebook → `.zip` of
  all chapters). Create/edit via modal (title + description), search,
  three-dot menu (Edit/Export/Delete) — not a bare delete button.
- **Tasks** — Kanban board, priority + due dates (with real overdue
  highlighting), recurring tasks (completing one auto-spawns the next
  occurrence), subtasks, overdue penalties (a real lazy-check on list,
  not dead code), project linking.
- **Gamification** — XP/levels/streaks/badges, wired to task completion.
  Badges seed defensively wherever they're checked (not just one startup
  hook) so they can't silently fail to award.
- **Journal** — entries with mood, wiki-link rendering (same component as
  Notes, resolved links clickable/navigable, unresolved ones inert since
  Journal has no notebook to create into), mood heatmap (GitHub-style,
  91 days).
- **Projects** — title + description (editable), linked tasks.
- **Search** — global keyword search across notebooks/chapters/tasks/
  journal, results are clickable and navigate somewhere real.
- **Knowledge Graph** — React Flow, nodes/edges across every entity type,
  empty-state message when there's nothing to show.
- **Dashboard** — 5 widgets, onboarding banner when the workspace is
  totally empty, "Tasks Due" sorted by real urgency (not creation order).
- **Timeline** — chronological, grouped by month.
- **Trash** — list/restore/permanently-delete, soft-delete everywhere.
- **Semantic search** (AI layer, Phase 1) — meaning-based search over
  note/journal content using a locally-run embedding model
  (`all-MiniLM-L6-v2`, no API key, no per-search cost). Content gets
  chunked (paragraph-based) and embedded on save; a Keyword/Semantic
  toggle sits in the existing GlobalSearch dropdown. See `backend/ai/`
  and §7 for the architecture reasoning and what's still deferred to
  Phase 2 (multi-provider chat-completion features).
- **Mobile responsive** down to ~375px — hamburger drawer nav, Notes/
  Projects use one-column drill-down with back buttons, Kanban scrolls
  horizontally instead of cramming 4 columns into a phone screen.
- **CI** — GitHub Actions, pytest + frontend build, runs on every push,
  currently green.

## What's NOT built (deliberately)

- **AI layer Phase 2** (chat-completion features — suggestions, study
  coach). Semantic search (Phase 1) is done; Phase 2 needs the
  multi-provider abstraction (Anthropic + OpenAI + Gemini + OpenAI-
  compatible registry for OpenRouter/NVIDIA NIM/Groq/etc., user-
  selectable) that was scoped in the AI-layer conversation but not yet
  built — see §7.
- **Real auth.** Single hardcoded default user
  (`backend/dependencies.py::get_current_user`). Fine for personal local
  use, would need real work before ever being multi-user or exposed to
  the internet. Explicitly kept out of scope for now even though the
  project is going open-source — flagged as a known limitation rather
  than solved.

---

## 4. How this project got here (session history)

**Session 1 — catastrophic data loss, then full rebuild.** The original
Stud-OS (a different, earlier build) was discovered to be 100% corrupted —
every single file zeroed out, including `node_modules` and `.venv`, with
no git history, no bytecode, no editor local-history to recover from.
Root cause never confirmed. Wrote `REBUILD_PLAN.md` forensically
reconstructing the original scope from surviving migration *filenames*
(the data was gone, but filenames like `add_gamification_tables` told us
what existed). Recovery failed, so the plan got executed for real:
fresh repo, pushed to GitHub from commit 1, then built the entire V1
feature set from scratch, phase by phase, each one tested before moving
on. See `REBUILD_PLAN.md`'s addendum for what deviated from the original
plan (no TipTap, no Zustand — simpler choices worked fine).

**Later sessions — hardening and polish**, roughly in this order:
1. Full manual QA pass seeding realistic data and clicking through every
   page — found and fixed a real bug (task priority sorting was
   alphabetical, not by severity, because SQL sorts enum columns as
   strings — "high" sorted after "low"). Added the `qa_check.py` e2e
   smoke test and a proper pytest suite (this is when automated testing
   was added — it caught two more real bugs immediately: a startup hook
   coupled to the wrong DB, and badges that could silently never award).
2. Closed out a list of "still not done" items in one pass: overdue
   penalty engine (was dead code — built but never called), chapter
   version history UI, real markdown rendering, mood heatmap, mobile
   responsiveness, CI, route-level code splitting (536KB bundle → 318KB).
3. Several rounds of UI feedback from screenshots, each one fixed and
   re-verified live: Notes not using full screen (a missing `flex-1`,
   genuine CSS bug), Notes' 3-column layout showing dead placeholder
   columns (redesigned to a focused drill-down, one view at a time),
   Graph having no empty-state message, notebook/chapter creation moved
   from inline input to a proper modal (title+description), chapter
   search added, "✕" replaced with a "⋯" menu (Edit/Export/Delete),
   export-to-file added. Found a real concurrency bug while testing this
   (`get_current_user` could 500 when parallel requests raced to create
   the default user on a fresh DB) — fixed with a proper race-safe
   get-or-create. Most recently: the "focused view" redesign was still
   centered in a narrow column instead of using full width — replaced
   with a responsive card grid, and bumped font sizes.
4. Moved the backend dev port from 8000 to 8420 — 8000 belongs to another
   project (Aether) on this machine.
5. **AI layer, Phase 1 (semantic search).** Had the architecture
   conversation before writing code, as planned: settled on embeddings
   always local (cost/privacy — search runs on every query, can't route
   that through a paid API and call it "near-zero cost"), paragraph-based
   chunking, brute-force cosine similarity (fine at personal scale, no
   vector index needed yet). Mid-conversation the user decided this is
   going open-source rather than staying personal-only, which added a
   requirement: many API providers, user-selectable, not hardcoded to
   Anthropic. Key design insight: most of the requested providers
   (OpenAI, OpenRouter, NVIDIA NIM, Groq) speak the same OpenAI-
   compatible wire format, so that's one generic adapter + a registry of
   presets, not N bespoke adapters — deferred to Phase 2 since it only
   matters for chat-completion features, not search. Built Phase 1 only
   this session: `Chunk` model (same polymorphic pattern as
   `Attachment`), local embedding pipeline, reindex hooks on chapter/
   journal create+update+restore, cleanup on trash's permanent delete,
   `GET /api/search/semantic`, frontend Keyword/Semantic toggle. Verified
   live via Playwright (searching "a function calling itself" correctly
   ranked a Recursion chapter over an unrelated Baking Bread one).
   Installed CPU-only torch explicitly — plain `pip install
   sentence-transformers` pulls ~2.5GB of CUDA packages this machine
   doesn't need. Mid-session the Desktop Commander connection dropped
   entirely (not just a flaky single call — several consecutive tool
   calls all timed out, including a trivial `get_config`); it recovered
   after the user restarted it, but the background dev server processes
   died with it and had to be restarted before continuing. 9 new tests,
   suite at 66/66; `qa_check.py` extended to 24 checks. Committed and
   pushed, CI green.

**The pattern that got established, worth continuing:** every change —
UI or backend — gets typechecked, run through pytest, and *actually
clicked through in a real browser via Playwright* before being called
done. Screenshots from the user get taken seriously and checked against
real pixel measurements (e.g. "is there a gap on the right" got verified
with literal box-coordinate math, not just a glance). Bugs found while
testing something unrelated get fixed in the same pass, not deferred.
Commits are small-ish and descriptive; every commit that touches
frontend or backend gets pushed and (now that CI exists) confirmed green
on GitHub Actions, not just locally.

---

## 5. Codebase orientation

```
backend/
  main.py              FastAPI app, router registration
  database/
    base.py             Base, TimestampedMixin, SoftDeleteMixin, UUIDPKMixin
    models/              one file per resource
    session.py           DB engine/session (CWD-independent path resolution)
  routers/              one file per resource, all under /api/*
  schemas/               Pydantic request/response models
  gamification/          xp_rules, engine, levels, badges, streaks, penalties
  utils/                 wiki_parser, recurrence
  alembic/versions/      migrations, applied in order
  tests/                 pytest suite (57 tests), isolated temp-DB fixture
  qa_check.py             e2e smoke test against a live server
  dependencies.py         get_current_user (single hardcoded user, race-safe)

frontend/src/
  components/            organized by feature (notes/, tasks/, journal/,
                          projects/, graph/, dashboard/, timeline/, trash/,
                          gamification/, attachments/, search/, shared/,
                          layout/)
  pages/                  one per route, mostly thin wrappers
  lib/                    API clients (one per resource) + a few hooks
                          (useIsMobile, useDebouncedValue, useResolvedWikiLinks)
  App.tsx                 route-level code splitting via React.lazy
```

Shared/reusable pieces worth knowing about before rebuilding something
that already exists: `components/shared/Modal.tsx`, `DropdownMenu.tsx`,
`WikiLinkText.tsx` (markdown + wiki-link rendering, used by both Notes
and Journal).

---

## 6. Environment quirks (save yourself time)

- **Desktop Commander (the tool used for shell/file access to this real
  machine) has periodic connection instability** — tool calls sometimes
  time out with "No result received... local MCP server may be
  unresponsive." When this happens: just retry the same call once or
  twice before assuming something's broken. Several times an action
  actually succeeded server-side despite the client reporting failure —
  after a timeout, re-check state (`git status`, `git log`, `ps aux`)
  before blindly redoing something, to avoid double-applying it.
  **This can escalate to a full drop**, not just one flaky call — several
  consecutive calls in a row (even a trivial `get_config`) can all time
  out identically, meaning the local MCP server itself went down, not
  just a single request. When that happens, tell the user directly and
  wait for them to restart it rather than continuing to retry
  indefinitely. When it comes back, background dev server processes from
  before the drop are likely dead too (confirm with `ps aux` before
  assuming they're still running) and need restarting.
- **Check for stale background processes before starting dev servers.**
  `nohup`'d `uvicorn`/`vite` processes from earlier sessions can survive
  a dropped connection and keep running, causing confusing "address
  already in use" errors or, worse, silently serving stale code. Always
  `ps aux | grep -E "uvicorn backend|vite --port"` before starting new
  ones, and kill stale ones first.
- **Clean up after testing**: `rm -f backend/stud_os.db`,
  `rm -rf frontend/dist`, `rm -rf backend/uploads/*` before committing —
  none of these are tracked, but leaving test data around between
  sessions is confusing.
- **`gh` CLI is authenticated** and has `workflow` scope now (needed a
  one-time interactive device-code login to get it — already done,
  shouldn't need to redo it). `gh run list` / `gh run view` work for
  checking CI status.
- **Other projects run on this machine** (`Aether` on port 8000/8010,
  `Project_Aware_Package_Intelligence_System` on 8765) — never touch
  their processes, only ever `pkill -f "uvicorn backend"` /
  `pkill -f "vite --port"` (specific enough to only match Stud-OS).

---

## 7. Natural next step

**AI layer Phase 2: the multi-provider abstraction.** Semantic search
(Phase 1) is done and always uses local embeddings, so this is unrelated
to that code. What's scoped but not built: an `AIProvider` interface
(`embed()`/`chat()`, implement only what a feature needs) with
`AnthropicProvider`, `GeminiProvider` (both native SDKs, different
message formats), and one generic `OpenAICompatibleProvider`
(parameterized by `base_url`) that covers OpenAI, OpenRouter, NVIDIA NIM,
Groq, and similar via a small registry of presets — adding "some other
popular provider" later should be a registry entry, not new code.
Provider selection stored in a new single-row `ai_settings` table, keys
via `.env` (never hardcoded — this matters more now that it's going
open-source). Once that scaffold exists, the actual Phase 2 features
(suggestions, study coach) can build on it. Don't just start writing code
for this — the provider list/shape was scoped in conversation, but the
concrete feature set (suggestions first? study coach first?) hasn't been
discussed yet.

Beyond that, nothing is currently broken or half-done. If the user
reports something feels off, the established pattern (see §4) is: look
at it live yourself (boot both servers, seed realistic data, click
through it, don't just read the code), verify with pixel math or actual
interaction if it's a layout complaint, fix, re-verify, test, commit,
push, confirm CI green.
