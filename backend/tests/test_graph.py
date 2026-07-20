def test_graph_includes_notebook_chapter_containment_edge(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C"}).json()

    graph = client.get("/api/graph").json()
    node_ids = {n["id"] for n in graph["nodes"]}
    assert nb["id"] in node_ids and ch["id"] in node_ids
    assert any(e["source"] == nb["id"] and e["target"] == ch["id"] and e["kind"] == "contains" for e in graph["edges"])


def test_graph_includes_wiki_link_edge(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    a = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "A"}).json()
    b = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "B", "content": "[[A]]"}).json()

    graph = client.get("/api/graph").json()
    assert any(e["source"] == b["id"] and e["target"] == a["id"] and e["kind"] == "wiki_link" for e in graph["edges"])


def test_graph_includes_project_task_containment(client):
    proj = client.post("/api/projects", json={"title": "P"}).json()
    task = client.post("/api/tasks", json={"title": "T", "project_id": proj["id"]}).json()

    graph = client.get("/api/graph").json()
    assert any(e["source"] == proj["id"] and e["target"] == task["id"] for e in graph["edges"])
