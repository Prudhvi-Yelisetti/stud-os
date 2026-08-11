import io
import os

from backend.routers import attachments as attachments_router


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


def test_permanently_deleting_a_chapter_also_removes_its_attachments(client, tmp_path, monkeypatch):
    """Attachment is polymorphic (owner_type/owner_id), same as Chunk --
    no ORM foreign key means no automatic cascade delete. Chunk cleanup
    was already wired into permanent-delete; attachment cleanup wasn't,
    so a permanently-deleted chapter's uploaded files silently stayed on
    disk forever and their DB rows became permanently orphaned."""
    monkeypatch.setattr(attachments_router, "UPLOAD_DIR", str(tmp_path))

    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C"}).json()
    files = {"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    att = client.post(
        "/api/attachments", params={"owner_type": "chapter", "owner_id": ch["id"]}, files=files
    ).json()
    assert os.listdir(tmp_path) != []

    client.delete(f"/api/notebooks/chapters/{ch['id']}")
    resp = client.delete(f"/api/trash/chapter/{ch['id']}")
    assert resp.status_code == 204

    assert os.listdir(tmp_path) == [], "file was left orphaned on disk"
    listed = client.get("/api/attachments", params={"owner_type": "chapter", "owner_id": ch["id"]}).json()
    assert listed == [], "attachment DB row was left orphaned"


def test_permanently_deleting_a_notebook_also_removes_its_chapters_attachments(client, tmp_path, monkeypatch):
    """Same bug, one level up: a notebook's chapters cascade-delete via
    the ORM relationship, but their attachments -- polymorphic, so no
    cascade -- need the same explicit cleanup already applied to chunks."""
    monkeypatch.setattr(attachments_router, "UPLOAD_DIR", str(tmp_path))

    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C"}).json()
    files = {"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    client.post(
        "/api/attachments", params={"owner_type": "chapter", "owner_id": ch["id"]}, files=files
    )

    client.delete(f"/api/notebooks/{nb['id']}")
    resp = client.delete(f"/api/trash/notebook/{nb['id']}")
    assert resp.status_code == 204

    assert os.listdir(tmp_path) == [], "file was left orphaned on disk"


def test_permanently_deleting_a_journal_entry_also_removes_its_attachments(client, tmp_path, monkeypatch):
    monkeypatch.setattr(attachments_router, "UPLOAD_DIR", str(tmp_path))

    entry = client.post("/api/journal", json={"title": "J", "content": "x", "entry_date": "2026-01-01"}).json()
    files = {"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    client.post(
        "/api/attachments", params={"owner_type": "journal", "owner_id": entry["id"]}, files=files
    )

    client.delete(f"/api/journal/{entry['id']}")
    resp = client.delete(f"/api/trash/journal/{entry['id']}")
    assert resp.status_code == 204

    assert os.listdir(tmp_path) == [], "file was left orphaned on disk"


def test_permanently_deleting_a_project_also_removes_its_attachments(client, tmp_path, monkeypatch):
    monkeypatch.setattr(attachments_router, "UPLOAD_DIR", str(tmp_path))

    proj = client.post("/api/projects", json={"title": "P"}).json()
    files = {"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    client.post(
        "/api/attachments", params={"owner_type": "project", "owner_id": proj["id"]}, files=files
    )

    client.delete(f"/api/projects/{proj['id']}")
    resp = client.delete(f"/api/trash/project/{proj['id']}")
    assert resp.status_code == 204

    assert os.listdir(tmp_path) == [], "file was left orphaned on disk"
