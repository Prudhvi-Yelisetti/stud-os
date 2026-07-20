def test_search_finds_matches_across_entity_types(client):
    nb = client.post("/api/notebooks", json={"title": "Zebra Notebook"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Zebra Chapter"})
    client.post("/api/tasks", json={"title": "Zebra Task"})
    client.post("/api/journal", json={"title": "Zebra Entry", "entry_date": "2026-07-19"})

    results = client.get("/api/search", params={"q": "Zebra"}).json()
    types_found = {r["type"] for r in results}
    assert types_found == {"notebook", "chapter", "task", "journal"}


def test_search_too_short_returns_empty(client):
    assert client.get("/api/search", params={"q": "a"}).json() == []


def test_search_no_match_returns_empty(client):
    assert client.get("/api/search", params={"q": "nonexistentxyz"}).json() == []
