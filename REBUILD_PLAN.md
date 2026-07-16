# Stud-OS — Rebuild Plan

_Written after the 2026-05-18 total data loss (every file in this repo was_
_found zeroed out; no git, bytecode, or editor history to recover from)._
_This plan exists so a rebuild can start immediately without re-deriving scope._

---

## 0. What we actually know survived

Nothing readable survived, but the **file/folder skeleton and migration**
**filenames** did (captured before the wipe was discovered). That's forensic
gold — it tells us what was *actually built* in V1, as opposed to what the
vision doc merely *aspires* to. This plan treats those as two separate
tiers: **Recovered V1 scope** (rebuild this first, it's proven-out) and
**Vision-doc V2/V3 scope** (design target, build after V1 is solid).

## 1. Recovered V1 scope (reconstructed from migration history)

The alembic migration filenames give a near-complete map of the real V1
data model, in order:

1. `initial_schema` — base schema (users)
2. `add_notebooks_chapters_whiteboards` → `add_notebook_chapter_whiteboard_tables`
   — **Notebook / Chapter / Whiteboard** as core entities
3. `add_tasks_table` — **Task**
4. `add_journal_entries` → `create_missing_journal_entries_table` —
   **JournalEntry** (recreated once, so watch for a migration-ordering bug)
5. `add_attachments_table` → `chapter_attachments` → `clean_attachments_schema`
   — **Attachment**, chapter-scoped, schema was reworked at least once
6. `projects_subtasks_attachments` — **Project** + **Subtask** entities
7. `add_tags` — **Tag** (shared/polymorphic tagging across entities)
8. `add_chapter_pinning` — pinned flag on Chapter
9. `add_chapter_links` — **wiki-links / backlinks** table between chapters
10. `add_updated_at_to_chapters` — timestamp tracking
11. `chapter_version_history` — **version history** for chapters
12. `add_gamification_tables` — XP / levels / badges / streaks
13. `add_penalty_priority_fields_to_task` — penalty + priority on Task
14. `add_task_repeat_and_scheduling_fields` → `add_repeat_schedule_fields_to_tasks`
    — recurring task scheduling (touched twice — likely iterated on)
15. `add_backlog_field_to_tasks` — backlog flag on Task
16. `add_trash_flags` → `add_whiteboard_trash_flags` — **soft-delete**
    pattern applied broadly, then extended to whiteboards specifically
Backend modules confirmed present (routers + matching models/schemas):
`notes`, `journal`, `tasks`, `projects`, `attachments`, `gamification`
(with `badges.py`, `engine.py`, `levels.py`, `penalties.py`, `streaks.py`,
`xp_rules.py` as separate files — a real rules engine, not inline logic),
`search`, `users`, plus a `utils/wiki_parser.py`. Notably **no** `graph.py`
or `ai.py` router existed yet — Knowledge Graph and AI Layer were frontend-
only or not started on the backend.

Frontend: `package.json` confirmed dependencies for TipTap, Zustand,
TanStack Query, axios, react-router-dom, and **React Flow** (the full
`@reactflow/*` family — core, background, controls, minimap, node-resizer,
node-toolbar — was actually installed and in `.vite/deps` cache, meaning
the graph view had gotten far enough to be wired into the dev build, not
just a stub folder). Component folders confirmed: `editor`, `graph`,
`journal`, `layout`, `notes`, `tasks`. No confirmed `projects`, `dashboard`,
`search`, `timeline`, or `gamification` folders.

**Conclusion:** V1 was further along than a bare skeleton — Notes with
notebooks/chapters/wiki-links/backlinks/version-history, a Task manager
with recurring schedules and a real gamification engine (XP/levels/badges/
streaks/penalties), a Journal, Projects with subtasks, tagging, attachments,
soft-delete everywhere, basic global search, and a Knowledge Graph view
that had gotten as far as being wired up with React Flow in the frontend
(even if the backend `graph.py` endpoint wasn't there yet). The AI layer
from the vision doc was not started.
## 2. Revised feature priorities

Rebuilding from zero is a chance to re-sequence, not just re-type the same
code. Priority order, and why:

**Tier 1 — rebuild first (this is what made it a usable daily tool):**
- Notebooks → Chapters → Wiki-links → Backlinks (the actual "second brain"
  core; everything else references this)
- Tasks (Kanban + recurring/scheduling + backlog + priority)
- Journal (daily entries; keep it simple before adding mood analytics)
- Tags (build as a shared/polymorphic table from day one, not bolted on
  later — last time it arrived after 5 other migrations)
- Soft-delete/trash flags (build into the base model mixin from day one,
  not retrofitted per-entity like last time — `add_trash_flags` then
  `add_whiteboard_trash_flags` shows it was added twice)

**Tier 2 — rebuild second (once Tier 1 is stable):**
- Projects + Subtasks + Attachments
- Gamification engine (XP/levels/badges/streaks/penalties) — keep it a
  separate `gamification/` package like before, that separation was good
- Global search (start literal/keyword; semantic search is a V2 item)
- Chapter version history

**Tier 3 — continue what was already started:**
- Knowledge Graph visualization — React Flow was already installed and
  wired into the frontend dev build, so this was further along than a
  stub. Finish the `graph.py` backend endpoint (nodes/edges over Notebook/
  Chapter/Task/Journal/Project) that never got built, then reconnect it.
- Dashboard (widgets over the above — cheap once APIs exist)
- Timeline explorer

**Tier 4 — explicitly defer (vision doc V2/V3, needs Tier 1-3 data first):**
- AI layer (suggestions, RAG, study coach) — needs a stable knowledge graph
  and enough real content in it to be useful; building it too early means
  building against a moving schema
- Local LLM/embeddings, semantic memory, voice interface, whiteboards,
  flashcards, agent workspace
## 3. Architecture (kept, with a few upgrades)

Keep the original stack — it was a sound choice and there's no reason to
relitigate it:

- **Backend:** FastAPI + SQLAlchemy + Alembic + SQLite (dev) → Postgres later
- **Frontend:** React + TypeScript + Vite + TailwindCSS + TanStack Query + axios
- **Editor:** TipTap (rich text, matches wiki-link/backlink needs)
- **Graph:** React Flow (already installed last time — reinstall the same set)
- **State:** Zustand
- **Routing:** react-router-dom

Upgrades this time, specifically to prevent a repeat of this incident and
to fix the two visible V1 rough edges (journal table recreated once, trash
flags retrofitted per-entity):

1. **Base model mixin** — every table gets `id`, `created_at`, `updated_at`,
   `is_trashed`/`trashed_at` from a shared `Base` class from migration #1,
   not added piecemeal per-entity later.
2. **One schemas/ file per resource**, not just for `notes` and `journal`
   like before — keeps request/response shapes explicit and testable.
3. **`.gitignore` correctly scoped from commit #1** — exclude
   `node_modules/`, `.venv/`, `__pycache__/`, `*.db` — and **push to a real
   GitHub remote before writing a single feature**, not after. See §6.
4. **A `scripts/backup.sh`** that tars the SQLite db + repo nightly to a
   second location. Cheap insurance against exactly what just happened.
## 4. Data model to recreate (concrete)

```
User          id, email, name, created_at, updated_at

Notebook      id, user_id, title, description, trash*, created_at, updated_at
Chapter       id, notebook_id, title, content(md), pinned, version, trash*,
              created_at, updated_at
ChapterLink   id, from_chapter_id, to_chapter_id   (wiki-link -> backlink)
ChapterVersion id, chapter_id, content_snapshot, created_at

Whiteboard    id, notebook_id, data(json), trash*, created_at, updated_at

Task          id, user_id, project_id?, title, description, status
              (backlog/todo/in_progress/done), priority, repeat_rule,
              scheduled_at, due_at, penalty_flag, trash*, created_at, updated_at

JournalEntry  id, user_id, title, content, mood, date, created_at, updated_at

Project       id, user_id, title, description, trash*, created_at, updated_at
Subtask       id, project_id or task_id, title, done, created_at

Attachment    id, owner_type, owner_id, file_path, filename, mime_type,
              created_at

Tag           id, name
TagLink       id, tag_id, taggable_type, taggable_id   (polymorphic)

XPLog         id, user_id, amount, reason, created_at
Level         id, user_id, current_level, current_xp
Badge         id, name, description, icon
UserBadge     id, user_id, badge_id, earned_at
Streak        id, user_id, streak_type, current_count, last_active_date
Penalty       id, user_id, task_id, amount, reason, created_at
```

All `trash*` fields = the shared soft-delete mixin from §3.
## 5. Build phases

**Phase 0 — Safety net (do this before writing any feature code):**
- `git init`, correct `.gitignore`, create a **private GitHub repo**, push
  immediately, commit early and often from here on
- `scripts/backup.sh` + a cron entry
- FastAPI skeleton (`main.py`, `database/base.py`, `database/session.py`),
  Alembic initialized, Vite+React+TS+Tailwind skeleton, both booting

**Phase 1 — Core knowledge layer:**
- Base mixin, User, Notebook, Chapter models + first migration
- Notebook/Chapter CRUD routers + schemas
- Wiki-link parser (`utils/wiki_parser.py`) + ChapterLink + backlinks endpoint
- Frontend: `layout` shell, `notes` views (notebook list, chapter editor
  via TipTap, backlinks panel)

**Phase 2 — Tasks + Gamification:**
- Task model (with repeat/priority/backlog from the start, not retrofitted)
- Kanban router + frontend `tasks` board
- `gamification/` package (xp_rules, engine, levels, badges, streaks,
  penalties) wired to task completion events

**Phase 3 — Journal, Tags, Trash:**
- JournalEntry model + router + frontend `journal` views
- Tag + TagLink (polymorphic) wired into Notes and Tasks immediately
- Global trash view (list + restore) using the shared mixin

**Phase 4 — Projects, Attachments, Search:**
- Project + Subtask, Attachment upload/storage
- Global search router (keyword first) + frontend search UI

**Phase 5 — Graph, Dashboard, Timeline:**
- `graph.py` router exposing nodes/edges across Notebook/Chapter/Task/
  Journal/Project — this is the one piece that was missing last time even
  though the frontend `graph` folder + React Flow were already in place
- Dashboard widgets; Timeline explorer

**Phase 6 — AI layer (vision doc V2, deferred):**
- Only start once Phases 1-5 are stable and there's real content to work
  against (embeddings/RAG need a populated graph to be worth building)
## 6. Where to start, concretely (first session checklist)

If the recovery attempt fails and this becomes a real from-scratch rebuild,
do these in order, in a **fresh, empty** `~/Projects/stud-os` (or a new
folder entirely, to avoid any leftover zero-byte files confusing tooling):

1. `mkdir stud-os && cd stud-os && git init`
2. Write `.gitignore` (node_modules/, .venv/, __pycache__/, *.db, .env)
   **before** anything else touches this folder
3. Create the GitHub repo and `git remote add origin ...` — push an empty
   initial commit right now, so there's always a remote copy from commit 1
4. Backend: `uv`/`venv` + FastAPI + SQLAlchemy + Alembic; scaffold
   `backend/main.py`, `backend/database/base.py`, `backend/database/session.py`
5. `alembic init` → first migration: base mixin + `User`
6. `git commit` (yes, already — small, frequent commits from the start)
7. Frontend: `npm create vite@latest frontend -- --template react-ts`,
   add Tailwind, add TanStack Query + axios + react-router-dom, add the
   `layout` shell
8. `git commit` again
9. Set up `scripts/backup.sh`, wire it to cron
10. Only now start Phase 1 feature work (Notebook/Chapter) from §5
## 7. Loss-proofing this time

The root cause of this incident is still unconfirmed (every file in this
one directory — including `node_modules` and `.venv` — was zeroed while
sibling project directories were untouched, and the single git commit was
made *after* the wipe, so git offered no protection). Whatever caused it,
the fix is the same regardless of cause:

- **Push to a remote from commit 1.** A local-only git repo is not a backup.
- **Commit small and often**, not one big commit at a checkpoint.
- **A nightly `scripts/backup.sh`** tarring the repo + DB to a second
  location (external drive, cloud storage, or even just a second local
  path) — this alone would have made today a non-event.
- Avoid running broad recursive shell operations (`find … -exec`, mass
  `cp`/`rsync`) directly against the live project root without a `--dry-run`
  pass first.

---
*This plan lives at `REBUILD_PLAN.md` in the project root. If recovery*
*succeeds, treat this as a retrospective/roadmap doc instead of a rebuild spec.*
