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


def test_version_history_records_every_content_edit(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": "v1"}).json()

    client.patch(f"/api/notebooks/chapters/{ch['id']}", json={"content": "v2"})
    client.patch(f"/api/notebooks/chapters/{ch['id']}", json={"content": "v3"})

    versions = client.get(f"/api/notebooks/chapters/{ch['id']}/versions").json()
    # current content ("v3") lives on the chapter, not in history -- only
    # the two prior states should be snapshotted
    snapshots = [v["content_snapshot"] for v in versions]
    assert snapshots == ["v2", "v1"]  # newest first


def test_restoring_a_version_snapshots_current_content_first(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": "v1"}).json()
    client.patch(f"/api/notebooks/chapters/{ch['id']}", json={"content": "v2"})

    versions = client.get(f"/api/notebooks/chapters/{ch['id']}/versions").json()
    v1_snapshot = next(v for v in versions if v["content_snapshot"] == "v1")

    restored = client.post(
        f"/api/notebooks/chapters/{ch['id']}/versions/{v1_snapshot['id']}/restore"
    ).json()
    assert restored["content"] == "v1"
    assert restored["version"] == 3  # v1 -> v2 -> restored-to-v1 is version 3

    # "v2" (the content we just replaced) should now be in history too --
    # restoring is not a destructive undo
    versions_after = client.get(f"/api/notebooks/chapters/{ch['id']}/versions").json()
    assert any(v["content_snapshot"] == "v2" for v in versions_after)


def test_restoring_resyncs_wiki_links(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    target = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Target"}).json()
    ch = client.post(
        f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": "[[Target]]"}
    ).json()
    client.patch(f"/api/notebooks/chapters/{ch['id']}", json={"content": "no link now"})
    assert client.get(f"/api/notebooks/chapters/{target['id']}/backlinks").json() == []

    versions = client.get(f"/api/notebooks/chapters/{ch['id']}/versions").json()
    old_version = next(v for v in versions if v["content_snapshot"] == "[[Target]]")
    client.post(f"/api/notebooks/chapters/{ch['id']}/versions/{old_version['id']}/restore")

    backlinks = client.get(f"/api/notebooks/chapters/{target['id']}/backlinks").json()
    assert any(b["id"] == ch["id"] for b in backlinks)


def test_restore_unknown_version_returns_404(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C"}).json()
    resp = client.post(f"/api/notebooks/chapters/{ch['id']}/versions/does-not-exist/restore")
    assert resp.status_code == 404
