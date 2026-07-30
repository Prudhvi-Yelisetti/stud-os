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
.venv/bin/python -m pytest                # 57 tests, isolated temp DB, safe anytime
.venv/bin/python backend/qa_check.py       # needs a running backend; 22-check e2e smoke test
cd frontend && npm run build               # tsc + vite build, catches type errors too
```

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
- **Mobile responsive** down to ~375px — hamburger drawer nav, Notes/
  Projects use one-column drill-down with back buttons, Kanban scrolls
  horizontally instead of cramming 4 columns into a phone screen.
- **CI** — GitHub Actions, pytest + frontend build, runs on every push,
  currently green.

## What's NOT built (deliberately)

- **AI layer** (vision doc V2 — suggestions, semantic search, study
  coach). Deferred on purpose until there's an actual architecture
  conversation about it (local LLM vs. API-based, cost, which model).
  This is the natural "what's next" — see §7.
- **Real auth.** Single hardcoded default user
  (`backend/dependencies.py::get_current_user`). Fine for personal local
  use, would need real work before ever being multi-user or exposed to
  the internet.

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

The AI layer (vision doc V2) is the obvious "what's next" — it's the one
deliberately-deferred piece, and there's now a populated graph to build
it against. That needs an actual architecture conversation first though:
local LLM vs. API-based (and if API-based, using what — the Anthropic API
directly?), cost tradeoffs, which model, how it hooks into the existing
FastAPI backend. Don't just start writing code for it — have that
conversation with the user first.

Beyond that, nothing is currently broken or half-done. If the user
reports something feels off, the established pattern (see §4) is: look
at it live yourself (boot both servers, seed realistic data, click
through it, don't just read the code), verify with pixel math or actual
interaction if it's a layout complaint, fix, re-verify, test, commit,
push, confirm CI green.
