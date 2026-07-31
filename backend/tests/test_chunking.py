from backend.ai.chunking import chunk_text, MAX_CHUNK_CHARS


def test_empty_content_yields_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_content_is_one_chunk():
    assert chunk_text("A single short paragraph.") == ["A single short paragraph."]


def test_splits_on_paragraph_breaks():
    content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    assert chunk_text(content) == ["First paragraph.", "Second paragraph.", "Third paragraph."]


def test_oversized_paragraph_is_split_and_repacked():
    # One sentence repeated well past MAX_CHUNK_CHARS, all in a single
    # paragraph (no blank-line breaks) -- must be split on sentence
    # boundaries, not left as one giant chunk.
    sentence = "This is a test sentence that repeats itself many times. "
    huge_paragraph = sentence * 30
    assert len(huge_paragraph) > MAX_CHUNK_CHARS

    chunks = chunk_text(huge_paragraph)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= MAX_CHUNK_CHARS + len(sentence)  # last packed sentence may push slightly over


def test_chunk_order_is_preserved():
    content = "Alpha section.\n\nBeta section.\n\nGamma section."
    chunks = chunk_text(content)
    assert chunks == ["Alpha section.", "Beta section.", "Gamma section."]
