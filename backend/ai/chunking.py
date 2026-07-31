"""
Splits note/journal content into embeddable chunks.

Whole-chapter embedding loses precision -- a long chapter covering three
subtopics gets one blurry vector that doesn't match a specific query well.
Chunking by paragraph (falling back to sentence-splitting for paragraphs
that are themselves too long) keeps each vector focused on one idea, and
each chunk carries enough surrounding text to be useful as a search
result on its own.
"""
import re

# Rough token estimate: ~4 chars/token for English text. Keeping chunks
# under this means each one is small enough to be a focused, specific
# search hit rather than a whole page of only-partially-relevant text.
MAX_CHUNK_CHARS = 800

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_text(content: str) -> list[str]:
    """
    Paragraph-based chunking with a size cap. Oversized paragraphs are
    further split on sentence boundaries and greedily packed back up to
    MAX_CHUNK_CHARS, so a chunk is never a single sentence unless the
    sentence itself is already huge. Empty/whitespace-only input yields
    no chunks.
    """
    content = content.strip()
    if not content:
        return []

    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT.split(content) if p.strip()]

    chunks: list[str] = []
    for para in paragraphs:
        if len(para) <= MAX_CHUNK_CHARS:
            chunks.append(para)
            continue

        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(para) if s.strip()]
        current = ""
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) > MAX_CHUNK_CHARS and current:
                chunks.append(current)
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(current)

    return chunks
