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
from backend.ai.providers.base import ProviderError
from backend.ai.json_reply import parse_json_reply

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ProviderStatus(BaseModel):
    key: str
    label: str
    configured: bool


class AISettingsOut(BaseModel):
    feature: str
    provider_key: str | None
    model_override: str | None


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


@router.get("/providers", response_model=list[ProviderStatus])
def list_providers():
    return list_providers_with_status()


@router.get("/settings/{feature}", response_model=AISettingsOut)
def get_settings(feature: str, db: Session = Depends(get_db)):
    row = db.query(AISettings).filter(AISettings.feature == feature).first()
    if row is None:
        return AISettingsOut(feature=feature, provider_key=None, model_override=None)
    return row


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
    return row


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
    from backend.ai.embeddings import cosine_similarity

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
    """Asks the configured provider what to work on next, given open
    tasks. Returns configured=False (not an error) if the 'suggestions'
    feature has no provider set yet."""
    settings_row = db.query(AISettings).filter(AISettings.feature == "suggestions").first()
    if settings_row is None or not settings_row.provider_key:
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
        provider = get_provider(settings_row.provider_key)
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
    'study' feature's configured provider. The correct answer and
    explanation are included in the response -- this is a single-user
    local app with no adversarial client, so there's no reason to pay
    for a second round trip just to grade an answer the frontend can
    check itself."""
    settings_row = db.query(AISettings).filter(AISettings.feature == "study").first()
    if settings_row is None or not settings_row.provider_key:
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
        provider = get_provider(settings_row.provider_key)
        reply = provider.chat(
            messages=[{"role": "user", "content": prompt}],
            system="You are a study-quiz generator. You only ever respond with raw JSON, never prose.",
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
