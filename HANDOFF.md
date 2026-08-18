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

**Packaged as a self-contained AppImage (session 12, §4).** One process,
one port — FastAPI serves the built frontend itself, no separate
frontend server, no manual migrations. `./packaging/appimage/build.sh`
→ `Stud-OS-x86_64.AppImage`. See README's "Packaged desktop app" section.

**API keys can be entered directly in Settings now (session 13, §4)** —
no more required manual `.env` editing, though it still works if you
prefer it. Keys still never touch the database, only `.env`.

**Provider Settings redesigned (session 14, §4):** an Add-API-key form
(provider select + key input + Connect), a global default provider used
by every feature, and per-feature override if wanted — replaces the old
"one row per provider" layout.

**Going open-source, not just personal use.** Decided in the AI-layer
conversation (§7) — this shapes design choices going forward: no
hardcoded secrets, provider abstraction so contributors/users bring
their own API keys, README should be written for someone else running
this, not just Prudhvi. Auth is *not* in scope yet (deliberately kept
single-user for now, see "What's NOT built"). **Refined later (session
16, §4): "open-source" turned out not to be quite the right word for
what was actually wanted.** The license landed on is source-available,
not open source — self-hosting and modifying your own copy are freely
permitted, but copying/redistributing/publishing the source requires
permission. Every design choice from this paragraph (no hardcoded
secrets, BYOK, a README written for someone else running it) still
holds exactly as before; only the legal framing around the source
itself changed. See LICENSE and README's License section.

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
.venv/bin/python -m pytest                # 144 tests, isolated temp DB, safe anytime
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
12. **Packaged as a self-contained AppImage.** User asked to "create an
    application for this product" -- clarified first rather than
    guessing (options: packaged desktop app / landing page / mobile app
    / something else), then built from Aether's proven
    `packaging/appimage/` pattern on this same machine as a reference,
    since it's already solved this exact problem once. Deliberately
    diverged from Aether's architecture in one important way: Aether
    runs backend and frontend as two separate processes (a plain
    `python -m http.server` for the static frontend), which only works
    because its frontend bakes in the backend's URL at build time.
    Stud-OS's frontend already calls relative `/api/...` paths (the dev
    proxy in vite.config.ts), so instead FastAPI itself now optionally
    serves the built frontend from the same process/port when a new
    `FRONTEND_DIST` env var is set (`backend/main.py`, a no-op when
    unset, i.e. every normal dev session) -- one process, one port, no
    build-time URL baking needed at all. Hit one real, easy-to-get-wrong
    detail while adapting Aether's `AppRun`: Stud-OS imports itself as
    the `backend` package (`from backend.database import ...`, same as
    dev requiring the repo root on the path), unlike Aether's flat
    `main.py`, so `--app-dir` has to point one level *above* the copied
    `backend/` folder, not at it -- caught by checking alembic.ini's
    `prepend_sys_path=.` (which also meant the seed-DB migration step in
    `build.sh` has to run with CWD at the repo root, exactly like the
    documented dev workflow, not via a hand-rolled PYTHONPATH). Also
    reapplied the CPU-only-torch-first fix (already documented in this
    file for plain dev installs) inside `build.sh`, since
    sentence-transformers pulls the same unwanted ~2.5GB of CUDA
    packages in a fresh packaging venv too. Found and fixed a real,
    unrelated doc bug along the way: README's backend-run instructions
    said `cd backend` then run `uvicorn backend.main:app`, which never
    actually worked, for the same package-layout reason as the AppRun
    detail above. 2 new tests (`test_frontend_static_serving.py`) cover
    both the static/SPA-fallback serving and that it's a true no-op
    without `FRONTEND_DIST`; suite at 104/104. **Fully built and
    live-verified end to end, not just written and assumed correct**:
    ran the real `build.sh` (hit a Desktop Commander drop mid-build --
    see §6 -- but the build had actually already finished successfully
    on the real machine by the time the tool connection recovered, so
    nothing was lost), then actually launched the resulting
    `Stud-OS-x86_64.AppImage` and, through a real browser: confirmed a
    fresh install seeds the DB and serves a working UI; confirmed a
    *hard* navigation to `/notes` (not a client-side link click) falls
    back to `index.html` correctly, which is the part that actually
    proves the packaging works, not just that React Router's client-side
    routing works; created a real notebook through the actual packaged
    binary and confirmed it persisted to
    `~/.local/share/Stud-OS/stud_os.db`; stopped and relaunched and
    confirmed existing data survives (the "only seed if missing" guard
    works); launched a second instance while one was running and
    confirmed it detects the conflict instead of erroring. Also
    generated an original SVG icon (open notebook + knowledge-graph
    motif) -- the first attempt got corrupted by a `write_file` call
    (silently garbled to 6 bytes of binary garbage), caught by checking
    the output before trusting it rather than assuming the write
    succeeded, fixed by rewriting via a shell heredoc instead -- now
    flagged in §6 for future sessions, since it wasn't written down
    anywhere in this file before. Committed, pushed, CI green.
13. **API keys directly from Settings, no more manual .env editing.**
    User found the real usability gap this created: Settings could pick
    which provider a feature uses, but the key itself still needed a
    text editor and a restart. Opened by actually noticing the packaged
    AppImage was running live in the user's browser (AppImageLauncher +
    a real Chrome tab) -- stopped it cleanly for dev work rather than
    just killing things blindly, since real usage was happening. Added
    `PUT /api/ai/providers/{key}/key`: writes into `.env`, deliberately
    still never into the database -- same boundary the provider system
    has had since Phase 2, just a friendlier way to reach it. Tested
    python-dotenv's own auto-discovery directly against this repo before
    trusting it and it came back empty even from the repo root, so
    `backend/ai/env_file.py` resolves the `.env` path explicitly instead
    (`ENV_FILE_PATH` override, else repo root) -- same "don't trust
    ambient discovery" reasoning as `session.py`'s DB path, and it
    mirrors how `DATABASE_URL` already works for the packaged app.
    `AppRun` updated to set `ENV_FILE_PATH` to the writable data dir,
    since keys entered through the packaged app can't write into the
    read-only AppImage tree. Settings page restructured into a
    "Providers" section (the new key fields, or a plain status line for
    Ollama/LM Studio, which don't take one) above the existing
    "Features" picker. 7 new tests -- every one explicitly points
    `ENV_FILE_PATH` at a `tmp_path` file via monkeypatch *before*
    touching anything, specifically so nothing in the suite can ever
    write to the real repo `.env`; checked by hand before and after the
    full run that it hadn't, not just assumed the isolation held. Suite
    at 111/111. Live-verified in a real browser against the real dev
    backend: typed a real-shaped key into Anthropic's field, watched
    "Configured" appear and the feature dropdowns unlock with no reload,
    confirmed the key actually landed in the real `.env` on disk,
    selected it for a feature and confirmed that persisted too, then
    clicked "Remove" and confirmed the key was cleared from disk and
    `configured` flipped back to `false`. Test key and the `.env` file
    it created were deleted afterward. **The packaged AppImage from
    session 12 was built before this change** -- it still only supports
    manual `.env` editing (inside its own data dir) until rebuilt; not
    done automatically since the user didn't ask for a rebuild this
    session, just the underlying feature. Committed, pushed, CI green.
14. **Rebuilt the AppImage, then redesigned provider Settings from
    scratch.** Two parts. First, closed out session 13's flagged
    staleness: user asked to rebuild -- noticed a leftover dev `vite`
    process still running from earlier testing and killed it first
    (build.sh also runs `npm run build` in that same directory), then
    re-ran `build.sh` (much faster than session 12's first run, pip's
    cache from before was still warm) and relaunched, confirming
    existing data survived and the new key-entry UI was actually present
    in the rebuilt binary. Second, and the bulk of the session: the user
    found the previous "show a row for all 12 providers" Settings layout
    genuinely wrong for how they wanted to use it -- wanted an
    "Add API key" button revealing a provider-select + key-input +
    Connect form instead, a list of only *connected* providers, and a
    global default with per-feature override. Asked one clarifying
    question before building anything (what "set one active" should
    actually mean, given the app already had per-feature pickers) rather
    than guessing at a data-model decision -- user picked "global
    default, features can still override." That answer mapped cleanly
    onto the existing schema with zero migrations: `"default"` is just
    another `AISettings` row, same table `suggestions`/`study`/`ask`
    already used. New `_resolve_provider(db, feature)` helper (a
    feature's own override if set, else the default, else nothing) got
    wired into the three *usage* endpoints, not just the settings
    GET/PUT -- resolving the default only at the settings layer while
    the actual task-suggestions/quiz/ask endpoints kept reading the raw
    per-feature `provider_key` directly would have left the feature
    silently broken exactly where it mattered. Found a real bug while
    live-testing the removal flow, not from reading the code: removing a
    key clears it from `.env` but nothing clears an `AISettings` row
    (default or override) that still names that provider, so
    `effective_provider_key` kept reporting a now-dead provider instead
    of falling through -- fixed by having the resolver check
    `is_configured()` at every step, not just whether a `provider_key`
    string exists, with a dedicated regression test
    (`test_removing_a_key_falls_through_instead_of_resolving_to_a_dead_provider`).
    Settings page rebuilt: `ProvidersSection` (connected list + inline
    Add-API-key form, each row's Edit/Remove/Set-as-default) sits above
    the existing `FeatureProviderPicker`s, which now show
    "Use default (X)" as their leading option instead of "Not
    configured". 6 new backend tests, suite at 116/116. Frontend
    typechecks and builds clean. Live-verified in a real browser against
    the real dev backend, start to finish: connected a key through the
    new form, set it default, watched all three feature dropdowns update
    live with no reload, explicitly overrode one feature and confirmed
    the others still inherited, then edited and removed the key and
    watched the UI fall back cleanly (no orphaned dropdown value, no
    crash) -- which is exactly what surfaced the dead-provider bug
    above. **AppImage not rebuilt again after this second round of
    changes** -- the one relaunched earlier in this session now predates
    the provider-settings redesign; rebuild before relying on the
    packaged app reflecting it. Committed, pushed, CI green.
15. **Found and fixed a real, silent storage-leak bug: orphaned
    attachments on permanent delete.** User asked to work on "a new
    feature or bug" without naming one -- scoped it by auditing routers
    that hadn't had a close look in recent sessions (Tasks, Notes,
    Journal, Search, Trash), since the last several sessions were all
    AI-layer work. Found it by reading `trash.py`'s `permanently_delete`
    carefully: `Attachment` is polymorphic (`owner_type`/`owner_id`),
    exactly like `Chunk` -- no ORM foreign key, nothing cascades
    automatically. Chunk cleanup was already correctly wired in;
    attachment cleanup simply wasn't, for any of the three owner types
    that can have attachments (chapter, journal, project) or for a
    notebook's cascaded chapters. Meant every permanently-deleted item
    with a file attached left that file on disk forever and its DB row
    permanently orphaned -- a real, silent, unbounded storage leak, not
    a hypothetical. Followed the "confirm the bug is real before fixing
    it" discipline properly: wrote 4 failing regression tests first
    (one per owner type), ran them against the *unpatched* code and
    watched them actually fail with real orphaned files in a `tmp_path`,
    only then fixed it -- new `delete_attachments_for()` in
    `routers/attachments.py` (same shape as the existing
    `delete_chunks_for`), wired into `trash.py` for all four cases.
    120/120 backend tests pass (4 new). Also verified end-to-end against
    the **real filesystem**, not just the test suite -- uploaded a real
    file to `backend/uploads/` through a live server, permanently
    deleted its chapter through the real API, confirmed the directory
    was completely empty afterward. Committed, pushed, CI green.
    **AppImage still not rebuilt** (now two sessions behind -- missing
    both session 14's Settings redesign and this fix); user explicitly
    asked to hold off on rebuilding until later.
16. **Rebuilt the AppImage, then resolved the license and v1.0 version
    tag.** User asked "is it a real productivity app, or anything
    missing" -- answered honestly rather than just reassuring: yes, it's
    real (verified via actual usage evidence throughout this file, not
    just claims), but flagged real gaps -- no sync/mobile access, no
    reminders/notifications, no calendar view, attachments only work on
    Notes despite the backend allowing them on journal/project too, and
    the still-open license/tag decision. User then asked to rebuild the
    AppImage (closing out session 15's staleness -- confirmed the
    rebuilt binary's data dir had no notebooks/tasks in it, and was
    upfront that this wasn't data loss from the rebuild -- that database
    file appears to have never actually held the earlier test content in
    the first place, likely conflated with separate dev-server testing
    in past sessions) and then move to licensing. For the license,
    user's stated goal ("people can use it and self-host it freely, but
    can't copy the code without permission") doesn't fit any standard
    open-source license -- MIT/Apache/GPL all explicitly grant copying
    and redistribution rights, just with different conditions. Flagged
    this honestly (with the standard "not a lawyer" caveat) rather than
    picking the closest standard license and calling it done, since it
    would have meant either misleading the user about what rights they
    were actually granting, or silently deciding for them that
    "source-available" was close enough to what they asked for.
    Landed on a custom source-available `LICENSE`: free to use, run, and
    self-host (including modifying your own copy) for any purpose, but
    copying/redistributing/publishing the source or its derivatives
    needs permission -- not OSI-approved open source. Updated every
    forward-facing "going open-source" reference in README and this
    file's §1 to match (historical session-history entries elsewhere in
    §4 describing what was decided *at the time* were deliberately left
    alone -- they were accurate then; rewriting past decisions to match
    a later refinement would falsify the history this file exists to
    preserve). Bumped `frontend/package.json` and `main.py`'s FastAPI
    `version=` to `1.0.0`, tagged `v1.0.0`, pushed the tag. Committed,
    pushed, CI green.
17. **API keys were never actually verified -- fixed.** User doubted
    whether "Connected" in Settings meant anything real, and was right
    to: `is_configured()` only ever checked `bool(os.environ.get(key))`
    -- presence of a non-empty string, never a real API call. A typo'd
    or already-revoked key would sit there reporting "Configured" until
    the first real feature call 502'd, and local servers (Ollama/LM
    Studio) were *always* reported connected with zero checking they
    were actually running. New `AIProvider.verify()` on all three
    adapters, implemented as a cheap `models.list()` call rather than a
    full chat completion -- fast and free-or-near-free on every
    supported provider, and doesn't risk hanging on a slow local model
    just to answer "is this connected" (worth remembering given how long
    a real local generation took to test back in session 10 -- a models
    list call sidesteps that entirely). Wired into `PUT
    .../providers/{key}/key` (a new key is verified for real before
    being reported as saved; on failure it's rolled back, never left
    half-saved) and a new standalone `POST .../providers/{key}/verify`
    that powers an on-demand "Test connection" button now shown on
    *every* connected row, closing the local-provider gap too. Frontend
    now surfaces the real backend error detail (FastAPI's
    `HTTPException(detail=...)`) instead of a generic string. 124/124
    backend tests pass (5 new). **Live-verified against real services on
    purpose, not mocks** -- this feature's entire point is distinguishing
    "looks configured" from "actually works", so mocking the
    verification itself would have proven nothing about whether it's
    real: submitted a genuinely fake Anthropic key through the real API
    and got Anthropic's actual 401 back, confirmed the key was never
    written to `.env`, confirmed the exact error renders in the real
    Add-API-key form in a real browser with the key still there to fix;
    tested "Test connection" against a real, running Ollama instance
    (succeeded), stopped Ollama and tested again (real connection-refused
    error), restarted Ollama afterward since it was running before this
    session touched it. Desktop Commander dropped once mid-session right
    before the final pre-commit test/build run -- nothing lost (confirmed
    via `git status` on reconnect, matching the by-now-established
    recovery pattern), just re-ran everything cleanly before committing.
    Committed, pushed, CI green. **AppImage not rebuilt for this session's
    change** -- not asked for this time.
18. **Rebuilt the AppImage (closing out session 17), then added model
    management and cleaned up error messages.** User asked to create a
    new AppImage -- built and launched it, confirmed via curl that the
    real (non-stub) `verify()`/model logic was present by testing against
    a genuinely offline Ollama and getting a real connection-refused
    error back, not a canned response. Then, from a screenshot of
    Settings, two related asks: the raw error dump on a failed key
    ("Error code: 401 - {'type': 'error', ...'message': 'invalid
    x-api-key'}...}") needed to be human-readable, and there was no way
    to pick which *model* a provider uses, only which provider. New
    `friendly_error(label, exc)` in `providers/base.py` (auth/rate-limit/
    connection errors get a clean canned message; otherwise extracts just
    the `message` field from a dict-shaped body, or trims the raw string
    as a last resort), used by every adapter's `chat()`/`list_models()`.
    Model management mirrors the existing provider-key architecture
    closely on purpose: new `AIModel` table (migration `8efd67ebff84`) --
    a user's own curated subset per provider, not a mirror of the full
    catalog; new `AIProvider.list_models()` on all three adapters, fetching
    the *real* live catalog via each SDK's own `models.list()` -- the
    same cheap call `verify()` already used, so `verify()` became a
    concrete base-class method built on `list_models()` instead of 3
    separate implementations, removing duplication and guaranteeing "is
    this connected" and "what models does it offer" can never disagree.
    Settings: each connected provider gets a "Models ▾" toggle beside its
    name (matching the user's literal "beside the name" ask) revealing
    added models (default-badged, removable, settable) and a "+ Add
    model" flow that fetches the live catalog rather than a hardcoded
    list. New `_resolve_model()`: a feature's own `model_override` wins,
    else the resolved provider's default *added* model, else nothing
    (unchanged prior fallback) -- wired into all three usage endpoints
    via `chat()`'s new `model` parameter, so "the default model from the
    default provider is the default for AI activities" is resolved at
    call time, not just displayed in Settings. Ask page got a real
    per-chat model picker (the literal "while chatting, select a model"
    ask) scoped to the active provider's added models; zero added models
    -> clicking prompts to add one in Settings with a working link,
    rather than silently doing nothing, per the user's explicit ask.
    139/139 backend tests pass (15 new). **Live-verified against a real,
    currently-running Ollama instance, not mocks** -- fetched its actual
    model catalog through the API, added one, confirmed it auto-defaulted
    (first model added always becomes default, so adding exactly one
    never leaves a provider with none), set Ollama as the global default
    and confirmed Ask's picker showed "Default (qwen3.5:9b)" pulled live
    from Settings, switched the default to LM Studio (which had zero
    added models) and confirmed Ask correctly showed "Select model" with
    the add-one-first prompt, and separately re-confirmed the cleaned-up
    error message against a real, deliberately-fake Anthropic key.
    Committed, pushed, CI green.
19. **Found and fixed a real, silent, browser-visible bug: every
    timestamp lost its UTC marker to the frontend.** User asked to work
    on "something else -- new feature or bug" again, without naming one
    -- scoped it by auditing the gamification engine (streaks, levels,
    badges, penalties), since that code hadn't had a close look in a
    long time and was flagged historically for exactly this kind of
    real bug (badge-seeding, priority-sort). Read through
    `penalties.py`'s overdue-detection query and got suspicious of a
    `Task.due_at < now` comparison mixing what might be a naive DB value
    against a tz-aware `datetime.now(timezone.utc)` -- confirmed
    empirically with a throwaway script *before* assuming anything: a
    tz-aware datetime written to a `DateTime(timezone=True)` SQLite
    column round-trips as tz-**naive** on read (a well-known
    SQLAlchemy+SQLite gotcha), and instance-level Python comparison
    against it raises `TypeError`. The specific query in
    `penalties.py` turned out safe (SQLAlchemy `.filter()` builds SQL,
    not a Python comparison), but chasing the same fact further via a
    live curl round-trip surfaced the actual bug: the API was
    serializing every timestamp with **no UTC marker at all**
    (`"2026-08-14T01:00:00"` instead of `"...+00:00"`) -- and a
    marker-less ISO string is parsed by JS `new Date(...)` as **local**
    time, not UTC, per spec. Due-date display and the Kanban board's
    "overdue" highlighting (§3's "real overdue highlighting" feature)
    were silently wrong by the browser's UTC offset for anyone not
    physically in UTC -- this machine included. Traced to
    `TimestampedMixin`/`SoftDeleteMixin` in `database/base.py` (affects
    `created_at`/`updated_at` on *every* table, not just tasks) plus
    `Task`'s three datetime columns -- the only two files in the whole
    codebase using `DateTime(timezone=True)`, confirmed by grep before
    fixing anything so the fix wouldn't miss a table. Fixed once,
    centrally, with a new `UTCDateTime` `TypeDecorator` (re-attaches UTC
    tzinfo on read, normalizes writes to UTC) rather than patching call
    sites -- same "fix it at the source, not every place it surfaces"
    reasoning as `friendly_error()` and `list_models()`/`verify()` in
    session 18. Confirmed via `alembic check` that no migration was
    needed (identical underlying SQL column type, purely a Python-level
    read/write behavior change) before assuming that and moving on.
    144/144 backend tests pass (5 new, exercising the real HTTP API
    round-trip, not constructed in memory, including that the
    overdue-penalty query still correctly detects a genuinely overdue
    task after the change). **Live-verified in a real browser, the part
    that actually mattered** -- created one task due 2 hours in the past
    and one due 6 hours in the future as real UTC timestamps, confirmed
    the Kanban board correctly showed "Overdue: 8/15/2026" on the first
    and plain "Due 8/15/2026" (not overdue) on the second. Hit a
    real-time-elapsed gotcha mid-verification worth remembering: a
    session interruption (background processes died, matching the
    usual container-reset pattern) meant enough wall-clock time passed
    that the *original* "future" test task's due date had for real
    become past by the time the browser check ran -- correctly
    recognized this as a stale test window, not a bug, and made a fresh
    pair of tasks against current time rather than trusting stale
    fixtures. Committed, pushed, CI green.
20. **Rebuilt the AppImage, and found a real packaging bug while doing
    it: an existing install's database never got migrated.** User asked
    to rebuild, update all the docs, and produce a fresh-session
    starting prompt. The rebuild itself surfaced something real rather
    than being a clean formality: launched the freshly-built AppImage
    against this machine's actual, already-existing data directory
    (not a throwaway fresh install) and hit a genuine 500 --
    `no such table: ai_models` -- confirmed via the real backend.log
    traceback before assuming anything. Root cause: `AppRun` only ever
    ran `cp seed.db` when no DB file existed yet; it never ran alembic
    against an *existing* DB on later launches, so any migration added
    after someone's first install (here, session 18's `ai_models`
    table) would never reach their real data, only ever a brand-new
    install's freshly-seeded one. Fixed by running `alembic upgrade
    head` against `DATABASE_URL` on every launch, right before starting
    uvicorn -- idempotent, so a no-op on an already-current DB costs
    nothing -- placed inside the "not already running" branch
    specifically so it can't race a concurrent instance's DB lock.
    Split migration output into its own `migrations.log`, since
    uvicorn's own log redirect was immediately truncating it otherwise.
    **Live-verified end to end against the real, existing install, not
    a fresh one**: confirmed the 500 before the fix, rebuilt, relaunched
    against the exact same data directory, confirmed the endpoint
    returned 200 and `alembic_version` in the actual `.db` file read the
    latest revision, and confirmed existing data (notebooks, tasks)
    survived the migration untouched. 144/144 backend tests pass
    (unaffected -- packaging-script-only change, no application code).
    README updated to describe the current state of Settings (key
    verification, "Test connection", model management) rather than the
    pre-session-17/18 description it still had, and to note the
    AppImage now self-migrates on every launch. Committed, pushed, CI
    green.
21. **Wired attachments into Journal and Projects, closing a gap flagged
    (but not acted on) since session 16.** User asked to scope the
    session myself. Opened by stopping the AppImage that was running
    live in the user's browser (confirmed it was genuinely idle before
    touching it, same courtesy as session 13) so the dev backend could
    use port 8420, then started fresh dev servers -- no stale processes,
    no container-reset signs this time. Picked the target by re-reading
    session 16's honest "what's missing" answer rather than inventing
    new busywork: "attachments only work on Notes despite the backend
    allowing them on journal/project too" was named there and never
    followed up on. Confirmed it was real before touching anything --
    `ALLOWED_OWNER_TYPES` in `routers/attachments.py` has included
    `project` and `journal` since session 15's orphaned-attachment fix,
    and `AttachmentPanel.tsx` already took a generic
    `chapter | project | journal` prop -- but `grep`ping every `.tsx`
    file showed it was only ever imported into `ChapterEditor`. This was
    a pure frontend wiring gap, zero backend changes needed. Added
    `<AttachmentPanel ownerType="project">` to the project detail view
    (between description and Tasks) and `<AttachmentPanel
    ownerType="journal">` to each journal entry card. 144/144 backend
    tests pass, unchanged (frontend-only diff); `npm run build` clean.
    **Live-verified in a real browser, both new surfaces, including the
    cascade-delete path this reuses from session 15**: created a real
    project, uploaded a real file through the new panel, confirmed it
    listed with a working download link, removed it and confirmed the
    file actually left `backend/uploads/`; created a real journal entry,
    uploaded a file to it, then specifically exercised the soft-delete →
    Trash → permanent-delete path (not just a direct removal) and
    confirmed the file was still present while the entry sat in Trash
    (soft delete correctly leaves attachments alone) and was gone from
    disk only after "Delete forever" -- proving `delete_attachments_for`
    fires correctly for these two owner types via the real trash flow,
    not just in the unit tests session 15 already wrote for it. All test
    data (project, journal entry, uploaded file) cleaned up afterward,
    confirmed via `GET /api/trash` returning empty and `uploads/` empty.
    No Desktop Commander drops this session. Committed, pushed, CI
    green. **AppImage not rebuilt** -- not asked for this time (now one
    session behind: missing this fix on top of already being one behind
    from session 20 being the last rebuild).
22. **User asked to make Stud-OS "do everything Obsidian does."** This
    needed pushback before any code, not after: Obsidian is a mature app
    built on a different foundation (plain markdown files as the source
    of truth, a community plugin ecosystem built over years) and full
    parity isn't a realistic scope for any single session. Laid out an
    honest gap analysis first (what's structurally different vs what's
    buildable as features), then had the user pick priorities rather
    than guessing: they picked all of tags/frontmatter, templates/daily
    notes, embeds, canvas, and live-preview editing as things they
    wanted eventually, then explicitly scoped *this session* to 1-2 of
    them, built fully and tested. Picked tags/properties + templates/
    daily-notes myself since embeds risked frontmatter-parsing edge
    cases better done after this session (see below) and canvas/
    live-preview are bigger, riskier undertakings (canvas is a new page
    type; live-preview means replacing the editor) better scoped on
    their own rather than folded in here.

    **Tags & frontmatter properties.** Found something genuinely
    interesting on the way in: `Tag`/`TagLink` tables already existed in
    the DB (migration `ed0790e1dedf`, "add tags, projects, tasks,
    journal, gamification") and the SQLAlchemy models were already
    imported in `models/__init__.py` -- scaffolded during the original
    rebuild and then completely unused ever since, not mentioned
    anywhere in this file. Built the real feature on top of those
    tables rather than adding new ones. `backend/utils/frontmatter.py`
    parses/serializes a YAML frontmatter block at the top of
    chapter/journal `content` -- frontmatter lives IN content, same
    philosophy as Obsidian's plain-file model, so there's no separate
    `properties` column and content stays the single source of truth
    (ChapterOut/JournalEntryOut expose `properties` and `tags` as
    Pydantic `computed_field`s derived from content, not stored
    columns). `backend/utils/tags.py` extracts tags from inline `#tags`
    (skipping fenced/inline code) unioned with a frontmatter `tags:`
    list. `backend/tag_indexing.py` keeps `TagLink` rows in sync,
    mirroring `backend/ai/indexing.py`'s Chunk reindexing pattern on
    purpose -- delete-then-recreate on every content change, called from
    the same create/update/restore-version call sites, plus wired into
    `trash.py`'s permanent-delete cascade (including the notebook-cascade
    path) so tag links can't orphan the way an earlier gap almost let
    attachments orphan before session 15's fix. New `GET /api/tags` and
    `GET /api/tags/{tag}` endpoints power a Tags page (cloud of all tags
    with counts, click through to a filtered list) -- the closest
    equivalent to Obsidian's tag pane. `PropertiesPanel` (shared between
    Notes and Journal) shows properties as editable key/value rows and
    saves through new `PATCH .../properties` endpoints that rewrite just
    the frontmatter block server-side, keeping the body untouched and
    going through the normal version-snapshot path.

    **Templates & daily notes.** `is_template` / `is_daily_template`
    boolean columns on `Chapter` (migration `40a47800da2d`). At most one
    chapter holds `is_daily_template` at a time, enforced in
    `update_chapter` by unsetting any previous holder -- same invariant
    shape as "exactly one default AI model" from session 18's settings
    page. `backend/utils/templates.py` interpolates `{{date}}`/
    `{{time}}`/`{{datetime}}` placeholders. New `GET
    .../chapters/templates` (list), `POST .../chapters/from-template/
    {id}` (create with interpolation), and `POST /api/daily-notes/today`
    (get-or-create today's chapter in an auto-created "Daily Notes"
    notebook, seeded from the designated daily template if one exists,
    idempotent within the same calendar day). Refactored chapter
    creation into a shared `create_chapter_record()` helper in
    `routers/notes.py` (no leading underscore, unlike the other private
    helpers there -- it's deliberately reused by `daily_notes.py`) so the
    plain-create, from-template, and daily-note paths can't drift out of
    sync with each other.

    **Process notes worth remembering:**
    - Made a real mistake partway through: used the sandbox `create_file`
      tool instead of Desktop Commander for 7 new backend files, so they
      landed in the sandbox instead of on this machine, while `edit_block`
      calls to *existing* files (which went through Desktop Commander
      correctly) ended up referencing modules that didn't exist yet.
      Caught it with a plain `ls` before running anything -- the fix is
      always to check, not to assume a tool call landed where intended.
      Recreated all 7 files through Desktop Commander and re-verified
      migration + imports + tests before moving on. **If a file you just
      created isn't where you expect it, check which tool wrote it.**
    - Two container/MCP-server disconnects happened mid-session --
      once mid-verification (dev servers gone, `/tmp` cleared, new
      `uptime -s`), once a genuine unresponsive-MCP-server hang where
      even a trivial `echo test` timed out on both Desktop Commander and
      Playwright and the honest move was to tell the user their local
      MCP servers needed a restart rather than keep silently retrying.
      Both times, recovery was the same: confirm the actual code
      survived on disk (`git status --short`), confirm DB/migration
      state (`alembic current`), restart both dev servers, re-verify
      before continuing -- nothing was lost either time, everything
      (including in-progress test data) had persisted to disk/DB.
    - Live browser testing earned its keep twice this session, not
      zero times: (1) frontmatter YAML was leaking into the rendered
      markdown preview -- `marked` read the block's own `---` lines as
      a setext heading, producing a garbled heading where the
      frontmatter should have been invisible. Fixed with a
      `stripFrontmatter()` frontend util applied to preview rendering
      (Notes and Journal) and the chapter-list snippet preview -- raw
      edit mode still shows full content, frontmatter included, on
      purpose. (2) `PropertiesPanel` committed on every individual input
      blur, which meant tabbing from the key field to the value field
      in the same row fired a premature commit with the value field
      still empty -- confirmed via the API directly (`version: 2`,
      `properties: {"mood": ""}`) rather than assumed from the UI after
      a tool disconnect interrupted the original test. Fixed by giving
      each row a ref and checking `e.relatedTarget` against it before
      committing, so a same-row focus move doesn't count as "done
      editing." Neither of these would have been caught by
      `pytest`+`build` alone -- both are the specific class of bug this
      project's "test AND click through live" convention exists to
      catch.

    All 44 new backend tests (21 pure-function on frontmatter/tag
    extraction, 23 API integration) pass alongside the existing 144
    (188/188 total). `npm run build` clean. Committed, pushed, CI green
    on both jobs. **AppImage rebuilt later this same session** -- see
    the addendum below; don't read the rest of this paragraph as current
    AppImage status. **Not done, deliberately out of scope this
    session** (from the user's own priority list): embeds/transclusion
    (`![[note]]`), canvas, live-preview WYSIWYG editing -- good
    candidates for a future session, each scoped on its own rather than
    bundled together.

    **Addendum, same session:** user explicitly asked to rebuild the
    AppImage afterward. Stopped the dev servers first (needed port
    8420), ran `./packaging/appimage/build.sh` clean, then launched the
    result against this machine's real, existing personal install at
    `~/.local/share/Stud-OS/stud_os.db` (not a throwaway test DB) to
    verify self-migration for real -- it went from `8efd67ebff84`
    straight to head `40a47800da2d` with existing data intact, exactly
    as session 20's self-migration fix intends. Clicked through Tags and
    Today in the real browser against that real install; Today actually
    created a live "Daily Notes" notebook + empty chapter in the user's
    real data (not a test DB), so deleted it again afterward via trash
    + permanent-delete to leave their real install exactly as found --
    creating throwaway verification data in a real personal database
    needs the same cleanup discipline as test data anywhere else, maybe
    more so. Stopped the AppImage after verifying rather than leaving it
    running, same as not leaving dev servers running unattended -- if
    the user wants it running, that's a one-click relaunch from the repo
    root (`./Stud-OS-x86_64.AppImage`). **AppImage is current as of this
    session** as a result -- see §7 for the usual caveat that this goes
    stale the moment a future session touches backend/frontend code
    without rebuilding.

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
  tests/                 pytest suite (144 tests), isolated temp-DB fixture
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

packaging/appimage/    build.sh, AppRun, .desktop, icon -- see §4
                        session 12 and README's "Packaged desktop app"
                        section. Output binary is gitignored, not
                        committed; .cache/ (appimagetool download) too.

Shared/reusable pieces worth knowing about before rebuilding something
that already exists: `components/shared/Modal.tsx`, `DropdownMenu.tsx`,
`WikiLinkText.tsx` (markdown + wiki-link rendering, used by both Notes
and Journal).

---

## 6. Environment quirks (save yourself time)

- **`desktop-commander:write_file` can silently corrupt binary/text
  content it doesn't like** — writing an SVG icon (session 12, §4) once
  produced a file that was supposed to be ~1KB of readable SVG markup
  but was actually 6 bytes of garbled binary, with no error reported.
  Don't trust a write succeeded just because the tool call returned
  cleanly, especially for anything binary-ish (images, icons) — verify
  the actual file content afterward (`head -c`, `file`, or an image
  view) before building on it. When a write matters and something
  outside plain UTF-8 text is involved, writing via a shell heredoc
  (`cat > file << 'EOF' ... EOF` through `start_process`) has been more
  reliable than `write_file` directly.

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

**Packaging (session 12, §4) is done and live-verified**: the app ships
as a real, working, self-contained AppImage
(`./packaging/appimage/build.sh` → `Stud-OS-x86_64.AppImage`), one
process/port, no manual setup on first launch, and now self-migrates an
existing install's database on every launch too (session 20, §4) so
updating to a newer build never leaves real data on an outdated schema.
Not yet done: no macOS or Windows packaging (Linux-only for now,
matching this machine), and the built binary isn't attached anywhere
yet -- distribution is via GitHub Releases once actually published (see
"License and version tag: resolved" below -- that decision itself is
done, publishing isn't). **The AppImage currently sitting in the repo
root should be current as of session 22** -- rebuilt at the end of that
session (see the addendum in §4) and live-verified against this
machine's real, existing data directory, including a real
self-migration from `8efd67ebff84` to head. Still worth checking the
most recent session in §4 before assuming so, though, since any session
after 22 that touches backend/frontend code without an explicit rebuild
will make this stale again -- that's the normal state between
rebuilds, not a bug.

**Settings can now do everything through the UI (sessions 13 and 14,
§4)**: connect a provider by pasting its key through an Add-API-key
form (no more manual `.env` editing required, though it still works if
preferred), set one connected provider as the global default, and
override that default per feature if wanted. Keys still never touch the
database, only `.env` -- session 14 only changed how the *choice* of
which provider each feature effectively uses gets resolved and
displayed, not where secrets live.

**A real bug got fixed outside the AI layer for the first time in a
while (session 15, §4):** permanently deleting a chapter, notebook,
journal entry, or project with an attached file used to leave the file
on disk and its DB row orphaned forever. Fixed; see `delete_attachments_for`
in `routers/attachments.py`. Worth remembering the *pattern* here more
than the specific fix: `Attachment` and `Chunk` are both polymorphic
(`owner_type`/`owner_id` or `parent_type`/`parent_id`), so anything else
built the same way in the future needs the same explicit cleanup on
permanent delete -- it will not cascade automatically just because a
"real" model like Chapter or Notebook does.

**Attachments now work on Journal and Projects too, not just Notes
(session 21, §4)**: this was a pure frontend gap -- the backend and the
`AttachmentPanel` component were already generic across all three owner
types since session 15, just never rendered outside `ChapterEditor`.
Fixed by adding the panel to `ProjectsView` and `JournalView`; no backend
change. If a fourth attachable entity type is ever added, remember it
needs three things to actually work end-to-end, not just the backend
piece: added to `ALLOWED_OWNER_TYPES`, wired into `delete_attachments_for`
callers in `trash.py`, and an actual `<AttachmentPanel>` rendered
somewhere in that entity's own UI -- this session is a reminder that the
first two being done doesn't guarantee the third followed.

**Model management exists now (session 18, §4)**: each connected
provider has its own curated list of added models (Settings' "Models ▾"
toggle), one marked default, fetched from the provider's real live
catalog rather than a hardcoded list. `_resolve_model()` in
`routers/ai.py` mirrors `_resolve_provider()`'s cascade exactly (feature
override → resolved provider's default added model → nothing). Ask has
its own per-chat model picker on top of that, scoped to whichever
provider is currently active. If a future provider adapter gets added,
it needs a real `list_models()` too (`verify()` is built on it now, not
separate) -- same "don't stub this out" reasoning session 17 already
established for `verify()` itself.

**Every timestamp is correctly UTC-marked now (session 19, §4)**: see
`UTCDateTime` in `database/base.py`. If a future model adds its own raw
`DateTime(timezone=True)` column instead of going through
`TimestampedMixin`/`UTCDateTime`, it'll silently reintroduce this exact
bug for that one column -- grep for `DateTime(timezone=True)` before
assuming a new datetime column is safe, or just use `UTCDateTime`
directly.

Beyond that, nothing is currently broken or half-done. If the user
reports something feels off, the established pattern (see §4) is: look
at it live yourself -- either the normal two-server dev setup or the
packaged AppImage, whichever fits what's being checked -- seed realistic
data, click through it, don't just read the code, verify with pixel math
or actual interaction if it's a layout complaint, fix, re-verify, test,
commit, push, confirm CI green.

**License and version tag: resolved (session 16, §4).** LICENSE exists
now — source-available, not standard open source (see §1's updated
note and README's License section). `package.json` and `main.py`'s
FastAPI `version=` should be bumped to `1.0.0` and a `v1.0.0` git tag
pushed as part of that same session — check §4's session 16 entry and
`git tag -l` to confirm whether that actually landed, rather than
assuming from this paragraph alone.

**"Configured" now means actually verified, not just non-empty (session
17, §4).** `AIProvider.verify()` (a cheap `models.list()` call, not a
full chat completion) backs both the Add-API-key flow -- a bad key
never gets saved -- and a new "Test connection" button on every
connected row, including Ollama/LM Studio, which previously reported
connected unconditionally with zero checking. If a future provider
adapter gets added, it needs a real `verify()` too, not a stub that
always returns success -- the whole point of this feature is that
"Configured" means something.
