"""
Keeps TagLink rows in sync with note/journal content, mirroring
backend/ai/indexing.py's Chunk reindexing pattern exactly: delete this
owner's existing links, re-derive from current content, recreate. Called
from the notes/journal routers on create, update (when content changes),
and version restore -- see reindex_tags(); and from trash on permanent
delete -- see delete_tag_links_for().

Tag and TagLink are pre-existing tables (migration ed0790e1dedf) that
were scaffolded during the original rebuild but never wired to any
feature until now -- see HANDOFF.md.
"""
from sqlalchemy.orm import Session

from backend.database.models.tags import Tag, TagLink
from backend.utils.frontmatter import parse_frontmatter
from backend.utils.tags import extract_tags


def reindex_tags(db: Session, *, taggable_type: str, taggable_id: str, content: str) -> None:
    db.query(TagLink).filter(
        TagLink.taggable_type == taggable_type, TagLink.taggable_id == taggable_id
    ).delete()

    properties, body = parse_frontmatter(content)
    names = extract_tags(body, properties)
    for name in names:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()  # need tag.id before the TagLink insert below
        db.add(TagLink(tag_id=tag.id, taggable_type=taggable_type, taggable_id=taggable_id))


def delete_tag_links_for(db: Session, *, taggable_type: str, taggable_id: str) -> None:
    db.query(TagLink).filter(
        TagLink.taggable_type == taggable_type, TagLink.taggable_id == taggable_id
    ).delete()
