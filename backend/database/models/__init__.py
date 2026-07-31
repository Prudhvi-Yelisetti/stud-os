"""Import every model here so Alembic autogenerate can see them all."""
from backend.database.models.user import User  # noqa: F401
from backend.database.models.notes import Notebook, Chapter, ChapterLink, ChapterVersion  # noqa: F401
from backend.database.models.tags import Tag, TagLink  # noqa: F401
from backend.database.models.projects import Project  # noqa: F401
from backend.database.models.tasks import Task, Subtask  # noqa: F401
from backend.database.models.journal import JournalEntry  # noqa: F401
from backend.database.models.gamification import (  # noqa: F401
    XPLog, Level, Badge, UserBadge, Streak, Penalty,
)
from backend.database.models.attachments import Attachment  # noqa: F401
from backend.database.models.ai import Chunk  # noqa: F401
