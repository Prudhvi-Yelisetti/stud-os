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
**AI layer is now fully built through Phase 4, plus three follow-up
sessions**: semantic search (Phase 1), provider abstraction + task
suggestions (Phase 2), study-coach quiz generation (Phase 3),
ask-your-notes RAG chat (Phase 4), a session-9 audit that fixed a
quiz-truncation bug and added markdown rendering to AI outputs, a
session-10 addition of Ollama/LM Studio as local, keyless providers, and
a session-11 addition of DeepSeek/Mistral/xAI/Perplexity — 12 providers
total now — see §3 and §7.

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
.venv/bin/python -m pytest                # 102 tests, isolated temp DB, safe anytime
.venv/bin/python backend/qa_check.py       # needs a running backend; 30-check e2e smoke test
cd frontend && npm run build               # tsc + vite build, catches type errors too
```
**`qa_check.py` is NOT idempotent** — it creates a "QA Task" with
`repeat_rule: daily` and never cleans it up, so running it twice against
the same dev DB without resetting will make the "recurring task spawned"
check fail (it'll count 2 instead of 1). Not a bug, just a smoke-test
limitation — wipe `backend/stud_os.db` and re-run migrations if you need
a clean run.

**AI provider keys (Phase 2/3/4 features only — semantic search doesn't
need any of this):** copy `.env.example` to `.env` and fill in whichever
provider(s) you want. `main.py` calls `load_dotenv()` before anything
reads the environment. Without a `.env`, `/api/ai/suggestions/tasks`
correctly reports `configured: false` rather than erroring — that's
expected, not broken.

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
  toggle sits in the existing GlobalSearch dropdown. See `backend/ai/`.
- **AI provider abstraction + task suggestions** (AI layer, Phase 2) —
  `backend/ai/providers/`: an `AIProvider` interface with Anthropic and
  Gemini native adapters plus one generic OpenAI-compatible adapter
  (covers OpenAI/OpenRouter/Groq/NVIDIA NIM via a registry of presets —
  adding another provider is a config entry, not new code). Settings
  page lets you pick a provider per feature; keys live in `.env`
  (`.env.example` documents all of them), never hardcoded. First feature
  built on it: task suggestions ("what should I work on next") on the
  dashboard. A separate "Related notes" panel in the chapter editor
  reuses Phase 1's embeddings directly — no provider involved, always
  free.
- **Study coach quiz generation** (AI layer, Phase 3) — `POST
  /api/ai/study/quiz/{chapter_id}` generates a multiple-choice quiz from
  a chapter's content via the "study" feature's configured provider
  (same per-feature settings pattern as Phase 2, no new plumbing). The
  answer + explanation come back in the same response rather than a
  second round-trip to grade — reasonable for a single-user local app.
  `backend/ai/json_reply.py` tolerates the markdown-fence-wrapping
  models often do despite being told not to. Frontend: a `QuizPanel` in
  the chapter editor, one question at a time with immediate feedback and
  a running score.
- **Ask-your-notes RAG chat** (AI layer, Phase 4) — `POST /api/ai/ask`:
  multi-turn chat that answers using the user's own notes/journal as
  context. Composes Phase 1 (local embeddings for retrieval) with
  Phase 2 (provider abstraction for generation), no new infrastructure —
  just a new `"ask"` feature key. Retrieval is scoped by a `sources`
  list (notebook ids, plus the literal `"journal"` sentinel since
  journal entries aren't inside a notebook; empty = search everything).
  Stateless server-side — the frontend holds and resends the full
  transcript each turn. Returns the distinct sources actually used per
  turn for citation display. Frontend: new `/ask` page with a source
  picker (notebook + Journal pills), chat UI, and clickable source tags
  under each answer that navigate to the note. See §7 for what's next.
- **Mobile responsive** down to ~375px — hamburger drawer nav, Notes/
  Projects use one-column drill-down with back buttons, Kanban scrolls
  horizontally instead of cramming 4 columns into a phone screen.
- **CI** — GitHub Actions, pytest + frontend build, runs on every push,
  currently green.

## What's NOT built (deliberately)

- **AI layer Phase 5+.** Semantic search, task suggestions, study
  quizzes, and ask-your-notes chat are all done — every idea from the
  original vision doc plus one the user added (RAG chat) is built now.
  The provider abstraction is reusable — a new Phase 5 feature just
  needs its own prompt-building + endpoint + UI. Nothing scoped for what
  that would even be; this is genuinely open territory, not a
  pre-set list to keep working through.
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
6. **AI layer, Phase 2 (provider abstraction + task suggestions).**
   Scoped in conversation first (feature: task suggestions; scope: build
   all 6 providers now, not incrementally). Built the `AIProvider`
   interface + registry + 3 adapters (Anthropic, Gemini, generic
   OpenAI-compatible), `ai_settings` table, and endpoints, backend
   fully tested before touching frontend (as agreed). Two real things
   found and fixed along the way, not pre-planned: (1) `python-dotenv`
   was in `requirements.txt` but nothing ever called `load_dotenv()` --
   `.env` had silently never been loaded anywhere in the app, which
   would have made the whole "keys go in .env" design not actually work.
   Fixed in `main.py`, added `.env.example`. (2) Sorting tasks by
   `Task.priority.desc()` for the suggestions prompt would have sorted
   alphabetically ("urgent" > "medium" > "low" > "high" — high sorts
   after low), not by actual severity; caught before it shipped and
   simplified to sort by due date, leaving priority for the LLM to
   reason over from the text instead of mis-sorting it procedurally
   (this exact enum-sorting trap is already flagged as a comment in
   `routers/tasks.py` from an earlier session — same bug shape twice).
   Frontend: Settings page (provider picker per feature), "Related
   notes" panel in the chapter editor (reuses Phase 1 embeddings
   directly, no provider), "What's Next" dashboard widget. Verified live
   with an actual (fake) key hitting the real Anthropic API to get a
   genuine failure response, which caught a real bug: the dashboard
   widget was mislabeling "the provider call actually failed" as "not
   configured yet" -- fixed to distinguish `isError` from
   `!data.configured`. Also discovered mid-session that the dev DB
   (`stud_os.db`) had lost its notebooks/chapters at some point across
   the connection drops (tasks/settings data in the same DB survived,
   so not a full wipe) -- not investigated further since it's disposable
   dev data, just re-seeded and moved on; noted here in case the pattern
   recurs and becomes worth digging into. The Desktop Commander
   connection dropped **twice more** this session (three total across
   Phase 1 + Phase 2), same full-drop pattern each time, recovering
   after the user restarted it. 11 new tests, suite at 77/77;
   `qa_check.py` extended to 28 checks (discovered and noted that
   `qa_check.py` isn't idempotent against a persistent dev DB -- see
   §2). Committed and pushed, CI green (both jobs, including the fresh
   `anthropic`/`google-genai`/`openai` installs in the CI environment).
7. **AI layer, Phase 3 (study coach quiz generation).** The user handed
   this one over fully ("plan yourself, do whatever works well") rather
   than co-scoping it -- picked the quiz feature since it was the
   original "study coach" idea from the vision doc and reuses Phase 2's
   provider abstraction directly (just a new `"study"` feature key, no
   schema change, no new provider plumbing). Designed the quiz to return
   the correct answer + explanation in the same response rather than a
   second round-trip to grade the user's pick -- fine for a single-user
   local app with no adversarial client. Built `backend/ai/json_reply.py`
   to tolerate the markdown-fence-wrapping models do to JSON despite
   being told not to. For live UI verification without a real API key,
   used a throwaway script (outside the repo, in `~/`, deleted after use)
   that monkeypatched `AnthropicProvider.chat` to return a canned quiz
   and ran the real `uvicorn` app against it -- let the actual frontend
   be clicked through end-to-end (question rendered, wrong-answer
   feedback + explanation shown, score tracked across questions) without
   touching any committed code or paying for a real API call. The
   Desktop Commander connection dropped once more this session (4th time
   total) with the same full-drop-then-clean-recovery pattern. Also hit
   (and fixed cleanly) the now-familiar "dev DB doesn't exist, run
   migrations first" issue from starting fresh after a previous
   session's cleanup -- see §2's note on `qa_check.py`/DB reset for the
   pattern. 12 new tests, suite at 89/89; `qa_check.py` extended to 29
   checks. Committed, pushed, CI green.
8. **AI layer, Phase 4 (ask-your-notes RAG chat).** User picked this
   direction after being offered a few options (RAG chat, journal
   insights, auto-tagging, spaced repetition), then co-scoped the
   specifics: multi-turn (not single-shot), sources shown, and
   user-selectable retrieval scope. Composed cleanly from what already
   existed -- Phase 1's embeddings for retrieval, Phase 2's provider
   abstraction for generation, no new infrastructure beyond one endpoint
   and a new `"ask"` feature key. Key design calls: sources is a flat
   `list[str]` where each entry is a notebook id or the literal string
   `"journal"` (journal entries aren't inside a notebook, so they needed
   their own sentinel rather than forcing an awkward parallel structure);
   empty list means "search everything" rather than some notebook being
   silently default-selected; the backend stays fully stateless and the
   frontend resends the whole transcript each turn, same as any ordinary
   chat client, so there's no new "conversations" table; history sent
   to the provider is capped to the last 8 messages so a long-running
   chat's token cost doesn't grow unbounded (the frontend still shows
   the full transcript). One test's own assumption was wrong rather than
   the code being wrong -- expected the baking-bread chapter to be
   excluded from an unscoped "top 6" retrieval, but the test corpus only
   had 3 chunks total, so everything trivially made top-6; fixed the
   test to check ranking order instead of exclusion. Live-verified the
   same way as Phase 3 (throwaway monkeypatch script outside the repo,
   deleted after use, no real API key needed) -- asked a real question
   through the real UI, got an answer with both a chapter and a journal
   source shown as clickable tags, clicked one and confirmed it
   navigated correctly, then re-verified that selecting only the Journal
   source correctly excluded the CS chapter from the next answer. The
   Desktop Commander connection dropped **twice** this session (5th and
   6th times total) -- the first of the two was a new failure mode: not
   just timeouts, but `tool_search` stopped finding Desktop Commander's
   tools at all and calling one by name failed immediately rather than
   timing out, meaning the MCP server had fully deregistered rather than
   just being slow to respond. Both times recovered cleanly after a
   restart with no work lost (everything from before each drop was
   already written and verified). 8 new tests, suite at 97/97;
   `qa_check.py` extended to 30 checks. Committed, pushed, CI green.
9. **AI layer audit + fixes.** User asked to go through the four AI
   features and improve them, without naming a specific target --
   scoped it myself by reading every file in `backend/ai/`, all three
   provider adapters, `routers/ai.py`, and the AI-related frontend
   (AskPage, QuizPanel, RelatedNotesPanel, TaskSuggestionWidget,
   SettingsPage) before deciding what was actually worth fixing, rather
   than inventing busywork. Found one real bug: `AnthropicProvider.chat()`
   had `max_tokens` hardcoded to 1024 -- a quiz with several questions
   (question + 4 choices + explanation each, as JSON) can exceed that,
   gets cut off mid-object, fails to parse, and surfaces as a confusing
   "invalid quiz" error rather than an obviously-a-length-problem one.
   Fixed by adding `max_tokens` to the `AIProvider.chat()` interface
   (default raised 1024 -> 4096) across all three adapters, and having
   the quiz endpoint scale its request with question count
   (`min(300 + count*350, 8192)`) instead of relying on the fixed
   default. Also fixed a real UX gap: AI replies (ask-notes answers,
   task suggestions, quiz explanations) were rendering literal `**`/`-`
   characters instead of formatted markdown -- built a shared
   `MarkdownText` component (deliberately simpler than `WikiLinkText`,
   no wiki-link resolution needed for AI output) and wired it into all
   three spots, plus added a manual refresh button to the task-suggestion
   widget so suggestions can be updated without waiting out the 5-minute
   `staleTime`. Considered adding a similarity-score threshold to
   related-notes/ask retrieval to cut noise from weakly-related results,
   but backed off -- the existing test
   (`test_ask_retrieves_relevant_context_and_returns_sources`)
   deliberately asserts that even a clearly unrelated chunk still shows
   up (just ranked lower), which is an intentional design choice for
   small personal corpora, not a bug; didn't want to fight that on a
   guess. 1 new backend test (suite at 98/98). Live-verified with the
   same throwaway-monkeypatch-script pattern as Phases 3/4 (seeded a
   real notebook/chapter/task via curl, patched `AnthropicProvider.chat`
   to return markdown-rich canned replies, clicked through the dashboard
   widget, the Ask page, and a full two-question quiz in a real browser)
   -- confirmed bold/italic/lists render correctly in all three spots
   and that quiz scoring, ask sources, and the new refresh button all
   still work. Script deleted after use, dev DB wiped, no stray
   processes left running, Aether's processes on 8000/8020 untouched
   throughout. No Desktop Commander drops this session. Committed,
   pushed, CI green.
10. **Local AI providers (Ollama, LM Studio).** User asked to verify all
    "popular" API options were covered and specifically named Ollama and
    LM Studio as missing. Both speak the OpenAI chat-completions API, so
    this reused `OpenAICompatibleProvider` as-is -- new registry entries,
    not new code, exactly the design intent already documented in
    `registry.py`'s module docstring. Two things the existing registry
    couldn't express and needed adding: `requires_key` (local servers
    don't check a key at all, so "configured" needed to stop meaning
    "has a real secret set" for these two) and `base_url_env_key` (so a
    local server on a non-default host/port -- Docker, LAN, custom port
    -- can be reached without editing code). 3 new tests, suite at
    101/101. Live-verified against a **real** local Ollama instance
    already running on this machine (not a monkeypatch this time --
    genuinely useful to have real hardware to test against): providers
    list correctly showed both as `configured: true` with zero `.env`
    changes, requesting a model that hadn't been pulled surfaced Ollama's
    own clean error message as a 502 (not a crash), and -- after Ollama
    stopped running partway through the session -- a plain "Connection
    error" 502, which is the realistic everyday case for a local
    provider and needed to degrade cleanly, not just the happy path.
    **Desktop Commander dropped once this session**, but with a new
    wrinkle worth flagging for future sessions: this time `Aether`'s
    processes (port 8000/8020) and the system's own locally-running
    Ollama service were *also* dead after recovery, and `uptime -s`
    showed a boot time essentially at "now" -- strong evidence the whole
    container was restarted, not just the MCP client reconnecting. This
    wasn't caused by anything run this session (Aether was never
    targeted by any command), but it's a stronger failure mode than the
    six previous drops, which only ever took out this project's own dev
    servers. Told the user directly rather than silently restarting
    Aether on their behalf, since it's not this project's process to
    manage. Committed, pushed, CI green.
11. **Restarted Aether + Ollama, then added 4 more hosted providers.**
    Opened by the user asking what was actually wrong with Aether/Ollama
    (from session 10's flagged container-restart theory) -- confirmed
    both still down, then restarted Aether's dev backend (known nohup
    command from session 10's notes) and its AppImage (found at
    `~/Aether-x86_64.AppImage`), and started Ollama via `ollama serve`
    (installed as a plain binary, not a systemd service). All three came
    up healthy. Then the actual task: user asked to add "all famous,
    mostly used" API providers. Researched current (Aug 2026) provider
    landscape via web search rather than relying on training-data
    knowledge, which would be stale for model names/endpoints in a
    fast-moving space -- confirmed exact base URLs and current default
    model names for each before adding anything. Added DeepSeek, Mistral
    AI, xAI (Grok), and Perplexity (Sonar) -- all four speak the OpenAI
    chat-completions format, so like Ollama/LM Studio before them this
    was registry entries, not new adapter code. Provider coverage is now
    12 total, which reasonably covers "all famous, mostly used" hosted
    + local options as of this writing. Added a new regression test that
    constructs a client for *every* `openai_compatible` preset in the
    registry (not just the new ones), so a typo'd env_key or base_url in
    a future addition fails a test instead of shipping silently. 1 new
    test, suite at 102/102. Live-verified via curl (provider list shows
    correct keys/labels) and a real browser (Settings page dropdowns
    show all four, correctly disabled without a key, exactly like the
    long-standing providers). Could not live-verify actual chat
    completions against these four specifically -- no real API keys for
    them were available this session, same "bring your own key" boundary
    as the original 6 hosted providers when they were first built.
    Ollama died again by the time cleanup ran (container reset between
    sessions, confirmed via `uptime -s` again, not something this
    session's commands caused) -- noted rather than chased, since
    restarting it wasn't part of what was asked this time. Committed,
    pushed, CI green.

**A pattern worth naming, now used three times (Phases 3, 4, and the AI
audit):** when no real API key is available for live-verifying a
provider-backed feature, monkeypatching the provider's `chat()` method in
a throwaway, never-committed script (run from outside the repo) and
pointing the real frontend at it is a good way to verify actual UI
behavior end-to-end without either skipping live verification or leaving
test scaffolding in the codebase. Delete the script after use; never let
anything like it get committed.

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
  tests/                 pytest suite (102 tests), isolated temp-DB fixture
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
  assuming they're still running) and need restarting. **This has now
  happened 6 times across 4 sessions** (once during Phase 1, twice
  during Phase 2, once during Phase 3, twice during Phase 4), each time
  recovering cleanly after a restart with no observed corruption to
  files already written -- but on one occasion the dev SQLite DB
  (`stud_os.db`) lost some rows (notebooks/chapters specifically; other
  tables in the same file were unaffected) across a drop+restart cycle,
  cause not identified. Since the dev DB is disposable this wasn't
  investigated further, but if it happens with something less
  disposable, dig into it properly rather than just re-seeding. **One
  occurrence was a different failure mode**: not a timeout, but
  `tool_search` stopped finding Desktop Commander's tools entirely and
  calling one directly by name failed immediately -- the MCP server had
  fully deregistered, not just gone slow. Same fix either way: tell the
  user, wait for a restart, don't keep retrying indefinitely. **A 7th
  occurrence (AI local-providers session, §4 session 10) showed a new,
  more severe variant**: not just this project's dev servers but
  `Aether`'s processes (a different project entirely, ports 8000/8020)
  and the machine's own Ollama service were also dead on recovery, and
  `uptime -s` showed a boot time right around the drop -- strong
  evidence the whole container got restarted that time, not just the
  MCP client reconnecting. Nothing run this session touched Aether. If
  this happens again: don't restart other projects' servers yourself
  (not this project's to manage) -- tell the user plainly what died so
  they can decide. **Session 11 confirmed this isn't only tied to
  Desktop Commander drops**: `uptime -s` showed another fresh boot at
  the *start* of that session, with no drop involved at all -- Aether
  and Ollama were already down before any tool even ran. This looks
  like the container recycling between sessions generally, not
  specifically an MCP-reconnect side effect. Practical takeaway: at the
  start of *any* session, don't assume background processes (this
  project's or others') survived from before -- check with `ps aux` /
  a health-check curl first, same as the existing stale-process check
  below, rather than only doing that check after an explicit drop.
- **Check for stale background processes before starting dev servers.**
  `nohup`'d `uvicorn`/`vite` processes from earlier sessions can survive
  a dropped connection and keep running, causing confusing "address
  already in use" errors or, worse, silently serving stale code. Always
  `ps aux | grep -E "uvicorn backend|vite --port"` before starting new
  ones, and kill stale ones first.
- **Clean up after testing**: `rm -f backend/stud_os.db`,
  `rm -rf frontend/dist`, `rm -rf backend/uploads/*` before committing —
  none of these are tracked, but leaving test data around between
  sessions is confusing. If you added a real (or fake, for testing) key
  to `.env` during a session, remove it too (`.env` is gitignored so it
  won't leak into a commit, but a stale fake key sitting there is
  confusing for the next session).
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

The AI layer now covers everything the original vision doc named, plus
one more the user asked for (ask-your-notes RAG chat), a full audit pass
(session 9, §4) that fixed a real quiz-truncation bug and a
markdown-rendering gap across all three AI-output surfaces, and two
rounds of provider expansion (sessions 10 and 11, §4) so the app can run
fully offline with no API key at all, or with whichever hosted provider
someone already has a key for. Provider coverage is now 12 total:
Anthropic, Gemini, OpenAI, OpenRouter, Groq, NVIDIA NIM, DeepSeek,
Mistral AI, xAI (Grok), Perplexity (Sonar), Ollama, LM Studio — a
genuinely broad spread of hosted and local options, reasonably close to
"every popular one" as of when this was written (model names/endpoints
in this space drift fast, so verify current details via web search
before adding another rather than trusting stale memory). There's no
queued "next AI feature" — this is genuinely open territory. If the user
wants more AI work, that means a fresh "what should this actually do"
conversation, not continuing down a pre-set list.

One thing flagged but deliberately *not* changed during the audit: the
"related notes" and "ask your notes" retrieval have no similarity-score
threshold, so a weakly- or un-related chunk can still show up (just
ranked lower) instead of being filtered out. This looked like a possible
quality improvement but existing test intent
(`test_ask_retrieves_relevant_context_and_returns_sources`) suggests it's
deliberate for small personal corpora, not an oversight — if it ever
becomes a real annoyance in practice, that's a "confirm with the user
first" conversation, not a unilateral fix.

Beyond that, nothing is currently broken or half-done. If the user
reports something feels off, the established pattern (see §4) is: look
at it live yourself (boot both servers, seed realistic data, click
through it, don't just read the code), verify with pixel math or actual
interaction if it's a layout complaint, fix, re-verify, test, commit,
push, confirm CI green.
