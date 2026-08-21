"""Integration tests for the Canvas feature: CRUD, JSON validation on
data, and trash/restore/permanent-delete."""
import json


def test_create_canvas_defaults_to_empty_graph(client):
    canvas = client.post("/api/canvases", json={"title": "My Board"}).json()
    assert canvas["title"] == "My Board"
    assert json.loads(canvas["data"]) == {}


def test_list_canvases_excludes_trashed(client):
    client.post("/api/canvases", json={"title": "Visible"})
    trashed = client.post("/api/canvases", json={"title": "Trashed"}).json()
    client.delete(f"/api/canvases/{trashed['id']}")

    titles = [c["title"] for c in client.get("/api/canvases").json()]
    assert "Visible" in titles
    assert "Trashed" not in titles


def test_update_canvas_data_round_trips(client):
    canvas = client.post("/api/canvases", json={"title": "Board"}).json()
    graph = {"nodes": [{"id": "n1", "type": "text", "x": 10, "y": 20, "text": "hello"}], "edges": []}

    updated = client.patch(f"/api/canvases/{canvas['id']}", json={"data": json.dumps(graph)}).json()
    assert json.loads(updated["data"]) == graph


def test_update_canvas_rejects_invalid_json(client):
    canvas = client.post("/api/canvases", json={"title": "Board"}).json()
    resp = client.patch(f"/api/canvases/{canvas['id']}", json={"data": "not valid json {"})
    assert resp.status_code == 422


def test_update_canvas_title_only(client):
    canvas = client.post("/api/canvases", json={"title": "Old Name"}).json()
    updated = client.patch(f"/api/canvases/{canvas['id']}", json={"title": "New Name"}).json()
    assert updated["title"] == "New Name"
    assert json.loads(updated["data"]) == {}  # untouched


def test_get_nonexistent_canvas_404s(client):
    resp = client.get("/api/canvases/does-not-exist")
    assert resp.status_code == 404


def test_trash_then_permanently_delete_canvas(client):
    canvas = client.post("/api/canvases", json={"title": "Temp"}).json()

    client.delete(f"/api/canvases/{canvas['id']}")
    trash = client.get("/api/trash").json()
    assert any(item["type"] == "canvas" and item["id"] == canvas["id"] for item in trash)

    client.delete(f"/api/trash/canvas/{canvas['id']}")
    assert client.get("/api/trash").json() == []
    assert client.get(f"/api/canvases/{canvas['id']}").status_code == 404


def test_restore_canvas_from_trash(client):
    canvas = client.post("/api/canvases", json={"title": "Restorable"}).json()
    client.delete(f"/api/canvases/{canvas['id']}")

    client.post(f"/api/trash/canvas/{canvas['id']}/restore")
    titles = [c["title"] for c in client.get("/api/canvases").json()]
    assert "Restorable" in titles
