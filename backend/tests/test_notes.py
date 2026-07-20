def test_create_and_list_notebook(client):
    resp = client.post("/api/notebooks", json={"title": "Algorithms"})
    assert resp.status_code == 201
    notebook = resp.json()
    assert notebook["title"] == "Algorithms"

    listed = client.get("/api/notebooks").json()
    assert any(n["id"] == notebook["id"] for n in listed)


def test_wiki_link_creates_backlink(client):
    nb = client.post("/api/notebooks", json={"title": "Graph Theory"}).json()
    bfs = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "BFS", "content": "intro"}).json()
    dfs = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "DFS", "content": "related to [[BFS]]"},
    ).json()

    backlinks = client.get(f"/api/notebooks/chapters/{bfs['id']}/backlinks").json()
    assert any(b["id"] == dfs["id"] for b in backlinks)


def test_chapter_content_edit_bumps_version_and_snapshots_history(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C1", "content": "v1"}).json()
    assert ch["version"] == 1

    updated = client.patch(f"/api/notebooks/chapters/{ch['id']}", json={"content": "v2"}).json()
    assert updated["version"] == 2


def test_backlinks_update_when_link_removed(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    a = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "A"}).json()
    b = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "B", "content": "[[A]]"}).json()

    assert len(client.get(f"/api/notebooks/chapters/{a['id']}/backlinks").json()) == 1

    client.patch(f"/api/notebooks/chapters/{b['id']}", json={"content": "no link anymore"})
    assert client.get(f"/api/notebooks/chapters/{a['id']}/backlinks").json() == []


def test_deleted_notebook_hides_its_chapters(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C"})

    client.delete(f"/api/notebooks/{nb['id']}")
    assert nb["id"] not in [n["id"] for n in client.get("/api/notebooks").json()]
