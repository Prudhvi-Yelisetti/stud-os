from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models.notes import Notebook, Chapter, ChapterLink
from backend.database.models.tasks import Task
from backend.database.models.projects import Project
from backend.database.models.journal import JournalEntry
from backend.database.models.user import User
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/graph", tags=["graph"])


class GraphNode(BaseModel):
    id: str
    type: str  # "notebook" | "chapter" | "task" | "project" | "journal"
    label: str
    parent_id: str | None = None  # e.g. chapter -> notebook, task -> project


class GraphEdge(BaseModel):
    source: str
    target: str
    kind: str  # "contains" | "wiki_link" | "belongs_to"


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


@router.get("", response_model=GraphResponse)
def get_graph(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Whole-system graph: Notebooks contain Chapters, Chapters wiki-link to
    each other, Projects contain Tasks. Journal entries are included as
    standalone nodes for now (linking them to chapters they mention is a
    V2 item once wiki-link syntax is extended to journal content).
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    notebooks = db.query(Notebook).filter(Notebook.user_id == user.id, Notebook.is_trashed.is_(False)).all()
    for nb in notebooks:
        nodes.append(GraphNode(id=nb.id, type="notebook", label=nb.title))

    chapters = (
        db.query(Chapter)
        .join(Notebook, Notebook.id == Chapter.notebook_id)
        .filter(Notebook.user_id == user.id, Chapter.is_trashed.is_(False))
        .all()
    )
    for ch in chapters:
        nodes.append(GraphNode(id=ch.id, type="chapter", label=ch.title, parent_id=ch.notebook_id))
        edges.append(GraphEdge(source=ch.notebook_id, target=ch.id, kind="contains"))

    chapter_ids = {ch.id for ch in chapters}
    links = db.query(ChapterLink).filter(ChapterLink.from_chapter_id.in_(chapter_ids)).all()
    for link in links:
        edges.append(GraphEdge(source=link.from_chapter_id, target=link.to_chapter_id, kind="wiki_link"))

    projects = db.query(Project).filter(Project.user_id == user.id, Project.is_trashed.is_(False)).all()
    for p in projects:
        nodes.append(GraphNode(id=p.id, type="project", label=p.title))

    tasks = db.query(Task).filter(Task.user_id == user.id, Task.is_trashed.is_(False)).all()
    for t in tasks:
        nodes.append(GraphNode(id=t.id, type="task", label=t.title, parent_id=t.project_id))
        if t.project_id:
            edges.append(GraphEdge(source=t.project_id, target=t.id, kind="contains"))

    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.user_id == user.id, JournalEntry.is_trashed.is_(False))
        .all()
    )
    for e in entries:
        nodes.append(GraphNode(id=e.id, type="journal", label=e.title))

    return GraphResponse(nodes=nodes, edges=edges)
