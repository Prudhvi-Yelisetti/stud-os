def test_permanent_delete_removes_item_completely(client):
    proj = client.post("/api/projects", json={"title": "P"}).json()
    client.delete(f"/api/projects/{proj['id']}")

    assert any(t["id"] == proj["id"] for t in client.get("/api/trash").json())

    resp = client.delete(f"/api/trash/project/{proj['id']}")
    assert resp.status_code == 204
    assert not any(t["id"] == proj["id"] for t in client.get("/api/trash").json())


def test_restore_unknown_type_returns_400(client):
    resp = client.post("/api/trash/not_a_real_type/some-id/restore")
    assert resp.status_code == 400


def test_restore_unknown_id_returns_404(client):
    resp = client.post("/api/trash/task/does-not-exist/restore")
    assert resp.status_code == 404


def test_chapter_trash_scoped_through_notebook_ownership(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C"}).json()

    client.delete(f"/api/notebooks/chapters/{ch['id']}")
    trash = client.get("/api/trash").json()
    assert any(t["type"] == "chapter" and t["id"] == ch["id"] for t in trash)

    client.post(f"/api/trash/chapter/{ch['id']}/restore")
    chapters = client.get(f"/api/notebooks/{nb['id']}/chapters").json()
    assert any(c["id"] == ch["id"] for c in chapters)
