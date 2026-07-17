import enum
from datetime import date as date_type

from sqlalchemy import String, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base, TimestampedMixin, SoftDeleteMixin, UUIDPKMixin


class Mood(str, enum.Enum):
    great = "great"
    good = "good"
    okay = "okay"
    bad = "bad"
    terrible = "terrible"


class JournalEntry(Base, UUIDPKMixin, TimestampedMixin, SoftDeleteMixin):
    __tablename__ = "journal_entries"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    mood: Mapped[Mood | None] = mapped_column(Enum(Mood), nullable=True)
    entry_date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
