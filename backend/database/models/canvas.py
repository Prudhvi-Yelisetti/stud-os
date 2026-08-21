from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base, TimestampedMixin, SoftDeleteMixin, UUIDPKMixin


class Canvas(Base, UUIDPKMixin, TimestampedMixin, SoftDeleteMixin):
    """A freeform visual board -- text notes and note-reference cards
    connected by edges, panned/zoomed like Obsidian's Canvas feature.
    `data` holds the whole node/edge graph as one JSON blob (matching
    Obsidian's own JSON Canvas format: one JSON document per canvas)
    rather than normalized node/edge tables -- there's nothing else that
    ever needs to query into a single node or edge, so per-row storage
    would only add cascade-delete plumbing for no real benefit."""

    __tablename__ = "canvases"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    data: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
