"""
Integration tests for semantic search. These load the real local embedding
model (see backend/ai/embeddings.py) -- first run downloads it, subsequent
runs use the HF cache, same as any other local-first ML dependency.
"""
def test_semantic_search_finds_conceptually_related_content(client):
    nb = client.post("/api/notebooks", json={"title": "Programming"}).json()
    client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={
            "title": "Recursion",
            "content": "A function that calls itself to solve smaller "
                       "instances of the same problem, with a base case "
                       "to stop the recursion.",
        },
    )
    client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={
            "title": "Baking",
            "content": "Preheat the oven to 350F and cream the butter "
                       "and sugar together until fluffy.",
        },
    )

    results = client.get("/api/search/semantic", params={"q": "a function calling itself"}).json()

    assert len(results) > 0
    assert results[0]["type"] == "chapter"
    assert results[0]["title"] == "Recursion"
    # The unrelated baking chapter should rank clearly behind the match,
    # not necessarily be absent (cosine similarity over short text rarely
    # goes near zero) -- what matters is that the real match sorts first.
    assert results[0]["score"] > 0.2


def test_semantic_search_empty_query_returns_empty(client):
    assert client.get("/api/search/semantic", params={"q": ""}).json() == []


def test_semantic_search_excludes_trashed_chapters(client):
    nb = client.post("/api/notebooks", json={"title": "Temp"}).json()
    ch = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "Doomed note", "content": "Extremely specific unique phrase about wombats."},
    ).json()

    before = client.get("/api/search/semantic", params={"q": "wombats"}).json()
    assert any(r["id"] == ch["id"] for r in before)

    client.delete(f"/api/notebooks/chapters/{ch['id']}")

    after = client.get("/api/search/semantic", params={"q": "wombats"}).json()
    assert not any(r["id"] == ch["id"] for r in after)


def test_reindex_on_content_edit_reflects_new_content(client):
    nb = client.post("/api/notebooks", json={"title": "Edits"}).json()
    ch = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "Mutable", "content": "Talking about giraffes and their long necks."},
    ).json()

    client.patch(
        f"/api/notebooks/chapters/{ch['id']}",
        json={"content": "Talking about penguins and the cold Antarctic."},
    )

    results = client.get("/api/search/semantic", params={"q": "penguins in Antarctica"}).json()
    assert any(r["id"] == ch["id"] for r in results)
