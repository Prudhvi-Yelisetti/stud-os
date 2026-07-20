import io

from backend.routers import attachments as attachments_router


def test_upload_list_download_delete_attachment(client, tmp_path, monkeypatch):
    monkeypatch.setattr(attachments_router, "UPLOAD_DIR", str(tmp_path))

    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C"}).json()

    files = {"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")}
    upload = client.post(
        "/api/attachments", params={"owner_type": "chapter", "owner_id": ch["id"]}, files=files
    ).json()
    assert upload["filename"] == "note.txt"
    assert upload["size_bytes"] == len(b"hello world")

    listed = client.get("/api/attachments", params={"owner_type": "chapter", "owner_id": ch["id"]}).json()
    assert any(a["id"] == upload["id"] for a in listed)

    download = client.get(f"/api/attachments/{upload['id']}/download")
    assert download.status_code == 200
    assert download.content == b"hello world"

    client.delete(f"/api/attachments/{upload['id']}")
    listed_after = client.get("/api/attachments", params={"owner_type": "chapter", "owner_id": ch["id"]}).json()
    assert listed_after == []


def test_upload_rejects_unknown_owner_type(client):
    files = {"file": ("x.txt", io.BytesIO(b"x"), "text/plain")}
    resp = client.post("/api/attachments", params={"owner_type": "bogus", "owner_id": "123"}, files=files)
    assert resp.status_code == 400
