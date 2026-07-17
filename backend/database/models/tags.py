from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampedMixin, UUIDPKMixin


class Tag(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)


class TagLink(Base, UUIDPKMixin, TimestampedMixin):
    """Polymorphic tag attachment: a tag applied to any taggable entity."""

    __tablename__ = "tag_links"

    tag_id: Mapped[str] = mapped_column(String(36), ForeignKey("tags.id"), nullable=False, index=True)
    taggable_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    taggable_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    tag: Mapped["Tag"] = relationship()
