from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.base import Base, TimestampedMixin, UUIDPKMixin


class User(Base, UUIDPKMixin, TimestampedMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
