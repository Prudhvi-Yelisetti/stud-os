"""
Chunk: a piece of a note/journal entry with its embedding vector, used for
semantic search. Polymorphic (parent_type/parent_id) like Attachment --
one table instead of one per source entity.

Embeddings are always generated locally (see backend/ai/embeddings.py);
this table has no notion of an API provider.
"""
from sqlalchemy import String, Text, Integer, JSON, ForeignKey
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
