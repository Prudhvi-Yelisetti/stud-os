"""Import every model here so Alembic autogenerate can see them all."""
from backend.database.models.user import User  # noqa: F401
from backend.database.models.notes import Notebook, Chapter, ChapterLink, ChapterVersion  # noqa: F401
