from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base, TimestampedMixin, UUIDPKMixin


class Attachment(Base, UUIDPKMixin, TimestampedMixin):
    """
    Polymorphic file attachment. owner_type/owner_id let this attach to
    any entity (chapter, project, journal entry) without a table per type.
    """
    __tablename__ = "attachments"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    owner_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    owner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
