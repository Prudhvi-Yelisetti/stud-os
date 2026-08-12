"""
AI features router. Two kinds of endpoint here, deliberately different in
cost/dependency:

- /suggestions/related/* -- reuses Phase 1's local embeddings, always
  available, no provider needed.
- /suggestions/tasks, /settings/* -- go through the provider abstraction
  in backend/ai/providers/; "no provider configured" is a normal 200
  response, not an error, since a fresh install has none set up.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.user import User
from backend.database.models.ai import AISettings, Chunk
from backend.database.models.tasks import Task, TaskStatus
from backend.database.models.notes import Chapter, Notebook
from backend.dependencies import get_current_user
from backend.ai.providers.factory import list_providers_with_status, get_provider, is_configured
from backend.ai.providers.registry import get_preset
from backend.ai.providers.base import ProviderError
from backend.ai.json_reply import parse_json_reply
from backend.ai.embeddings import embed_text, cosine_similarity
from backend.ai.env_file import upsert_key

router = APIRouter(prefix="/api/ai", tags=["ai"])

# "default" is stored as an AISettings row exactly like any real feature
# (suggestions/study/ask) -- reusing the existing table rather than adding
# a new one. Its own provider_key IS the global default; it has no further
# fallback of its own (see _resolve_provider).
DEFAULT_FEATURE = "default"


def _resolve_provider(db: Session, feature: str) -> str | None:
    """A feature's effective provider: its own explicit override if one is
    set AND still actually configured, else the global default (same
    condition), else None. This is what "add a global default, but let
    each feature override it if wanted" actually means at read time -- a
    feature with no explicit choice isn't "unconfigured", it just inherits
    whatever the default is right now, and picks up any later change to
    that default automatically.

    The is_configured() checks matter for a real, not-just-theoretical
    case: a provider's key can be removed (Settings' "Remove" button)
    without anything clearing the stored provider_key that pointed at it
    -- an override or default naming a now-unconfigured provider should
    fall through, not be reported as usable and fail at call time."""
    row = db.query(AISettings).filter(AISettings.feature == feature).first()
    if row and row.provider_key and is_configured(row.provider_key):
        return row.provider_key
    if feature == DEFAULT_FEATURE:
        return None
    default_row = db.query(AISettings).filter(AISettings.feature == DEFAULT_FEATURE).first()
    if default_row and default_row.provider_key and is_configured(default_row.provider_key):
        return default_row.provider_key
    return None


class ProviderStatus(BaseModel):
    key: str
    label: str
    configured: bool
    requires_key: bool


class ProviderKeyIn(BaseModel):
    # Empty string or omitted clears the key rather than setting an
    # empty one -- "remove my key" is a real, distinct action from the
    # UI (a "Remove" button posts this), not just an edge case to reject.
    api_key: str | None = None


class AISettingsOut(BaseModel):
    feature: str
    provider_key: str | None  # explicit override for this feature; None = inherits the default
    model_override: str | None
    effective_provider_key: str | None = None  # override if set, else the global default, else None


class AISettingsUpdate(BaseModel):
    provider_key: str | None = None
    model_override: str | None = None


class RelatedNoteOut(BaseModel):
    type: str
    id: str
    title: str
    snippet: str
    score: float


class TaskSuggestionsOut(BaseModel):
    configured: bool
    suggestion: str | None = None


class QuizQuestion(BaseModel):
    question: str
    choices: list[str]
    correct_index: int
    explanation: str


class QuizOut(BaseModel):
    configured: bool
    questions: list[QuizQuestion] = []


class AskMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class AskIn(BaseModel):
    messages: list[AskMessage]
    # Each entry is a notebook id, or the literal string "journal" (journal
    # entries aren't inside a notebook, so they need their own sentinel).
    # Empty list means "search everything" -- there's no forced default
    # selection the user has to first opt out of.
    sources: list[str] = []


class AskSourceOut(BaseModel):
    type: str
    id: str
    title: str


class AskOut(BaseModel):
    configured: bool
    answer: str | None = None
    sources: list[AskSourceOut] = []


@router.get("/providers", response_model=list[ProviderStatus])
def list_providers():
    return list_providers_with_status()


@router.put("/providers/{provider_key}/key", response_model=ProviderStatus)
def set_provider_key(provider_key: str, payload: ProviderKeyIn):
    """Writes (or clears) one provider's API key into the .env file --
    the Settings UI's alternative to hand-editing .env yourself. Never
    stored in the database: same "keys never touch the DB" boundary the
    provider abstraction has had since it was first built, just with a
    friendlier way to get the key into the one place it's ever read
    from. Takes effect immediately (no restart) -- see env_file.py.

    Setting a (non-empty) key is verified with a real, cheap request
    before it's reported as configured -- a typo'd or revoked key would
    otherwise sit there silently reporting "Configured" until the first
    real feature call failed with a 502. On verification failure, the
    key is rolled back (never left half-saved) and the request itself
    fails with a clear reason. Clearing a key (empty/omitted) skips
    verification -- there's nothing to verify when removing something."""
    preset = get_preset(provider_key)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Unknown provider '{provider_key}'")

    if payload.api_key:
        upsert_key(preset.env_key, payload.api_key)
        try:
            get_provider(preset.key).verify()
        except ProviderError as e:
            upsert_key(preset.env_key, None)  # roll back -- don't leave an unverified key saved
            raise HTTPException(status_code=502, detail=f"Could not verify this key: {e}")
    else:
        upsert_key(preset.env_key, payload.api_key)

    return {
        "key": preset.key, "label": preset.label,
        "configured": is_configured(preset.key), "requires_key": preset.requires_key,
    }


@router.post("/providers/{provider_key}/verify", response_model=ProviderStatus)
def verify_provider(provider_key: str):
    """On-demand 'Test connection' for a provider that already reports
    configured=True -- including local servers (Ollama/LM Studio), which
    is_configured() always reports as configured without ever checking
    they're actually running. Doesn't touch .env either way; this only
    answers "does this work right now", it doesn't change what's saved."""
    preset = get_preset(provider_key)
    if preset is None:
        raise HTTPException(status_code=404, detail=f"Unknown provider '{provider_key}'")

    try:
        get_provider(preset.key).verify()
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "key": preset.key, "label": preset.label,
        "configured": is_configured(preset.key), "requires_key": preset.requires_key,
    }


@router.get("/settings/{feature}", response_model=AISettingsOut)
def get_settings(feature: str, db: Session = Depends(get_db)):
    row = db.query(AISettings).filter(AISettings.feature == feature).first()
    provider_key = row.provider_key if row else None
    model_override = row.model_override if row else None
    return AISettingsOut(
        feature=feature, provider_key=provider_key, model_override=model_override,
        effective_provider_key=_resolve_provider(db, feature),
    )


@router.put("/settings/{feature}", response_model=AISettingsOut)
def update_settings(feature: str, payload: AISettingsUpdate, db: Session = Depends(get_db)):
    if payload.provider_key is not None and not is_configured(payload.provider_key):
        raise HTTPException(
            status_code=400,
            detail=f"'{payload.provider_key}' has no API key set -- add it to .env first",
        )

    row = db.query(AISettings).filter(AISettings.feature == feature).first()
    if row is None:
        row = AISettings(feature=feature)
        db.add(row)

    row.provider_key = payload.provider_key
    row.model_override = payload.model_override
    db.commit()
    db.refresh(row)
    return AISettingsOut(
        feature=row.feature, provider_key=row.provider_key, model_override=row.model_override,
        effective_provider_key=_resolve_provider(db, feature),
    )


@router.get("/suggestions/related/{chapter_id}", response_model=list[RelatedNoteOut])
def related_notes(
    chapter_id: str, limit: int = 5, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Nearest-neighbor lookup over existing embeddings -- no provider,
    no extra cost, works out of the box."""
    source_chunks = (
        db.query(Chunk)
        .filter(Chunk.user_id == user.id, Chunk.parent_type == "chapter", Chunk.parent_id == chapter_id)
        .all()
    )
    if not source_chunks:
        return []

    # Average this chapter's own chunk vectors into one query vector, then
    # search against everything else. Simpler than ranking per-source-chunk
    # and merging, and good enough at chapter-length content.
    dim = len(source_chunks[0].embedding)
    avg = [sum(c.embedding[i] for c in source_chunks) / len(source_chunks) for i in range(dim)]

    all_chunks = db.query(Chunk).filter(Chunk.user_id == user.id).all()

    seen_parents: set[str] = {chapter_id}
    scored: list[tuple[Chunk, float]] = []
    for c in all_chunks:
        if c.parent_id in seen_parents:
            continue
        scored.append((c, cosine_similarity(avg, c.embedding)))
    scored.sort(key=lambda pair: pair[1], reverse=True)

    results: list[RelatedNoteOut] = []
    used_parents: set[str] = set()
    for chunk, score in scored:
        if chunk.parent_id in used_parents:
            continue
        used_parents.add(chunk.parent_id)
        results.append(RelatedNoteOut(
            type=chunk.parent_type, id=chunk.parent_id, title=chunk.parent_title,
            snippet=chunk.content[:200], score=round(score, 4),
        ))
        if len(results) >= limit:
            break

    return results


@router.get("/suggestions/tasks", response_model=TaskSuggestionsOut)
def task_suggestions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Asks the effective provider (this feature's own override, else the
    global default) what to work on next, given open tasks. Returns
    configured=False (not an error) if nothing resolves at all."""
    provider_key = _resolve_provider(db, "suggestions")
    if not provider_key:
        return TaskSuggestionsOut(configured=False)

    open_tasks = (
        db.query(Task)
        .filter(Task.user_id == user.id, Task.is_trashed.is_(False), Task.status != TaskStatus.done)
        .order_by(Task.due_at.is_(None), Task.due_at)
        .limit(20)
        .all()
    )
    if not open_tasks:
        return TaskSuggestionsOut(configured=True, suggestion="No open tasks -- nothing to suggest.")

    task_lines = "\n".join(
        f"- {t.title} (status: {t.status.value}, priority: {t.priority.value}"
        + (f", due: {t.due_at.date()}" if t.due_at else "")
        + ")"
        for t in open_tasks
    )
    prompt = (
        "Here are my open tasks:\n\n" + task_lines +
        "\n\nWhich one or two should I focus on next, and why? Keep it to 3-4 sentences."
    )

    try:
        provider = get_provider(provider_key)
        reply = provider.chat(
            messages=[{"role": "user", "content": prompt}],
            system="You are a concise, practical productivity assistant inside a personal task manager.",
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return TaskSuggestionsOut(configured=True, suggestion=reply)


@router.post("/study/quiz/{chapter_id}", response_model=QuizOut)
def generate_quiz(
    chapter_id: str, count: int = 5, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Generates a multiple-choice quiz from a chapter's content via the
    'study' feature's effective provider (its own override, else the
    global default). The correct answer and explanation are included in
    the response -- this is a single-user local app with no adversarial
    client, so there's no reason to pay for a second round trip just to
    grade an answer the frontend can check itself."""
    provider_key = _resolve_provider(db, "study")
    if not provider_key:
        return QuizOut(configured=False)

    chapter = (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Chapter.id == chapter_id, Notebook.user_id == user.id)
        .first()
    )
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    if not chapter.content.strip():
        raise HTTPException(status_code=400, detail="This chapter has no content to quiz on yet")

    count = max(1, min(count, 10))
    prompt = (
        f"Study material, titled \"{chapter.title}\":\n\n{chapter.content}\n\n"
        f"Write exactly {count} multiple-choice questions testing understanding of this "
        "material. Respond with ONLY valid JSON, no markdown fences, no commentary, in "
        'exactly this shape: {"questions": [{"question": str, "choices": [4 strings], '
        '"correct_index": int (0-3), "explanation": str}]}'
    )

    try:
        provider = get_provider(provider_key)
        reply = provider.chat(
            messages=[{"role": "user", "content": prompt}],
            system="You are a study-quiz generator. You only ever respond with raw JSON, never prose.",
            # Scale the reply budget with question count -- a fixed cap sized
            # for a couple of questions truncates a 10-question quiz mid-JSON,
            # which fails to parse and shows up as a confusing "invalid quiz"
            # error rather than an obviously-a-length-problem one.
            max_tokens=min(300 + count * 350, 8192),
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    try:
        parsed = parse_json_reply(reply)
        questions = [QuizQuestion(**q) for q in parsed["questions"]]
        for q in questions:
            if not (0 <= q.correct_index < len(q.choices)):
                raise ValueError("correct_index out of range")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not generate a valid quiz: {e}")

    return QuizOut(configured=True, questions=questions)


@router.post("/ask", response_model=AskOut)
def ask_notes(payload: AskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Retrieval-augmented chat over the user's own notes and journal.
    Retrieval always uses local embeddings (Phase 1, free); generation
    goes through the 'ask' feature's effective provider (its own
    override, else the global default). Stateless -- the frontend holds
    and resends the full message history each turn, same as any ordinary
    chat client; nothing is persisted server-side."""
    provider_key = _resolve_provider(db, "ask")
    if not provider_key:
        return AskOut(configured=False)

    if not payload.messages or payload.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="messages must end with a user message")

    question = payload.messages[-1].content
    source_set = set(payload.sources)  # empty set = no filter = everything

    chunks = db.query(Chunk).filter(Chunk.user_id == user.id).all()
    if source_set:
        # Chunk doesn't store notebook_id directly (it's polymorphic, see
        # database/models/ai.py), so resolve chapter->notebook once here
        # rather than per-chunk.
        chapter_notebook = {
            c.id: c.notebook_id
            for c in db.query(Chapter).join(Notebook, Notebook.id == Chapter.notebook_id)
            .filter(Notebook.user_id == user.id).all()
        }
        allowed_notebooks = source_set - {"journal"}
        include_journal = "journal" in source_set

        def in_scope(chunk: Chunk) -> bool:
            if chunk.parent_type == "journal":
                return include_journal
            if chunk.parent_type == "chapter":
                return chapter_notebook.get(chunk.parent_id) in allowed_notebooks
            return False

        chunks = [c for c in chunks if in_scope(c)]

    answer_sources: list[AskSourceOut] = []
    context = ""
    if chunks:
        query_vector = embed_text(question)
        scored = sorted(chunks, key=lambda c: cosine_similarity(query_vector, c.embedding), reverse=True)
        top = scored[:6]

        seen_parents: set[str] = set()
        context_parts = []
        for chunk in top:
            context_parts.append(f'From "{chunk.parent_title}":\n{chunk.content}')
            if chunk.parent_id not in seen_parents:
                seen_parents.add(chunk.parent_id)
                answer_sources.append(AskSourceOut(type=chunk.parent_type, id=chunk.parent_id, title=chunk.parent_title))
        context = "\n\n".join(context_parts)

    system = (
        "You answer questions using ONLY the notes provided below as context. "
        "If the answer isn't in them, say so plainly rather than guessing. "
        "Be concise.\n\n" + (context if context else "(No matching notes were found for this question.)")
    )

    # Cap history sent to the provider -- a long-running chat shouldn't grow
    # the token cost of every single turn without bound. The frontend still
    # displays the full transcript; this only trims what gets sent upstream.
    history = [m.model_dump() for m in payload.messages[-8:]]

    try:
        provider = get_provider(provider_key)
        reply = provider.chat(messages=history, system=system)
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return AskOut(configured=True, answer=reply, sources=answer_sources)
