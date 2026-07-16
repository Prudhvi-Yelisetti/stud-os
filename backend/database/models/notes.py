from sqlalchemy import String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base, TimestampedMixin, SoftDeleteMixin, UUIDPKMixin


class Notebook(Base, UUIDPKMixin, TimestampedMixin, SoftDeleteMixin):
    __tablename__ = "notebooks"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    chapters: Mapped[list["Chapter"]] = relationship(back_populates="notebook", cascade="all, delete-orphan")


class Chapter(Base, UUIDPKMixin, TimestampedMixin, SoftDeleteMixin):
    __tablename__ = "chapters"

    notebook_id: Mapped[str] = mapped_column(String(36), ForeignKey("notebooks.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    notebook: Mapped["Notebook"] = relationship(back_populates="chapters")
    versions: Mapped[list["ChapterVersion"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan"
    )
    outgoing_links: Mapped[list["ChapterLink"]] = relationship(
        back_populates="from_chapter",
        foreign_keys="ChapterLink.from_chapter_id",
        cascade="all, delete-orphan",
    )


class ChapterLink(Base, UUIDPKMixin, TimestampedMixin):
    """A wiki-link from one chapter to another. Backlinks are the reverse query."""

    __tablename__ = "chapter_links"

    from_chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapters.id"), nullable=False, index=True
    )
    to_chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapters.id"), nullable=False, index=True
    )

    from_chapter: Mapped["Chapter"] = relationship(
        back_populates="outgoing_links", foreign_keys=[from_chapter_id]
    )


class ChapterVersion(Base, UUIDPKMixin, TimestampedMixin):
    """Snapshot of a chapter's content, taken on each meaningful edit."""

    __tablename__ = "chapter_versions"

    chapter_id: Mapped[str] = mapped_column(String(36), ForeignKey("chapters.id"), nullable=False, index=True)
    content_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    chapter: Mapped["Chapter"] = relationship(back_populates="versions")
