"""
Local embedding model, loaded once per process. all-MiniLM-L6-v2 is small
(~80MB), needs no GPU, and encodes a chunk in milliseconds -- fast enough
to run on every note save without the user noticing, and free forever
(no API key, no per-search cost).
"""
from functools import lru_cache

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so importing this module (e.g. for type checking or
    # in tests that don't touch embeddings) doesn't pay the torch import
    # cost or require the model to be downloaded.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings. Returns one vector (list[float]) per input,
    same order. Empty input returns an empty list without loading the model."""
    if not texts:
        return []
    vectors = _get_model().encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_text(text: str) -> list[float]:
    """Embed a single string (e.g. a search query)."""
    return embed_texts([text])[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors, in [-1, 1]."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
