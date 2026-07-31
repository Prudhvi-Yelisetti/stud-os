"""
Keeps the Chunk table in sync with note/journal content. Called from the
notes/journal routers on create, update (when content changes), and
version restore -- see reindex(); and from trash on permanent delete --
see delete_chunks_for().
"""
from sqlalchemy.orm import Session

from backend.database.models.ai import Chunk
from backend.ai.chunking import chunk_text
from backend.ai.embeddings import embed_texts, embed_text, cosine_similarity


def reindex(db: Session, *, user_id: str, parent_type: str, parent_id: str, parent_title: str, content: str) -> None:
    """Replace this parent's chunks with freshly embedded ones from its
    current content. Safe to call on every save -- delete-then-recreate
    is simpler than diffing, and cheap at chapter/entry scale."""
    db.query(Chunk).filter(Chunk.parent_type == parent_type, Chunk.parent_id == parent_id).delete()

    pieces = chunk_text(content)
    if not pieces:
        return

    vectors = embed_texts(pieces)
    for i, (piece, vector) in enumerate(zip(pieces, vectors)):
        db.add(Chunk(
            user_id=user_id,
            parent_type=parent_type,
            parent_id=parent_id,
            parent_title=parent_title,
            chunk_index=i,
            content=piece,
            embedding=vector,
        ))


def delete_chunks_for(db: Session, *, parent_type: str, parent_id: str) -> None:
    db.query(Chunk).filter(Chunk.parent_type == parent_type, Chunk.parent_id == parent_id).delete()


def semantic_search(db: Session, *, user_id: str, query: str, limit: int = 10) -> list[tuple[Chunk, float]]:
    """Embed the query and rank all of the user's chunks by cosine
    similarity. Brute-force -- fine at personal-notebook scale (see
    HANDOFF.md AI layer notes); swap in a vector index later if a
    workspace ever grows past tens of thousands of chunks."""
    query_vector = embed_text(query)
    chunks = db.query(Chunk).filter(Chunk.user_id == user_id).all()
    scored = [(c, cosine_similarity(query_vector, c.embedding)) for c in chunks]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:limit]
