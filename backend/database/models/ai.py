"""
Chunk: a piece of a note/journal entry with its embedding vector, used for
semantic search. Polymorphic (parent_type/parent_id) like Attachment --
one table instead of one per source entity.

Embeddings are always generated locally (see backend/ai/embeddings.py);
this table has no notion of an API provider.
"""
from sqlalchemy import String, Text, Integer, JSON, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base, TimestampedMixin, UUIDPKMixin


class Chunk(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "chunks"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    parent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    parent_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    parent_title: Mapped[str] = mapped_column(String(255), nullable=False)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Stored as a plain JSON array of floats. Brute-force cosine similarity
    # over these is fine at personal-notebook scale (see HANDOFF/AI layer
    # notes) -- a dedicated vector index is a drop-in upgrade later if a
    # workspace ever gets large enough to need one.
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)


class AISettings(Base, UUIDPKMixin, TimestampedMixin):
    """One row per feature (e.g. "suggestions"), recording which provider
    that feature should use. A feature with no row -- or a row with
    provider_key=None -- is a valid "not configured yet" state, not an
    error. Providers themselves are defined in backend/ai/providers/."""
    __tablename__ = "ai_settings"

    feature: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    provider_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_override: Mapped[str | None] = mapped_column(String(100), nullable=True)


class AIModel(Base, UUIDPKMixin, TimestampedMixin):
    """A model a user has explicitly added for one provider -- e.g.
    "claude-sonnet-4-6" under provider_key="anthropic". Providers list
    dozens of models via their real API (see AIProvider.list_models());
    this table is the user's own curated subset, not a mirror of that
    full catalog. Exactly one row per provider_key should have
    is_default=True at a time -- enforced in routers/ai.py's mutation
    endpoints, not at the DB level, same pattern as AISettings.feature
    being effectively-singleton per value without a state machine."""
    __tablename__ = "ai_models"
    __table_args__ = (UniqueConstraint("provider_key", "model_id", name="uq_ai_models_provider_model"),)

    provider_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_id: Mapped[str] = mapped_column(String(150), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
