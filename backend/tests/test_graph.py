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


def test_wiki_link_edge_appears_once_target_is_created(client):
    """Regression test: a chapter's outgoing links only get re-derived
    when THAT chapter is itself saved -- so linking to a note before it
    exists left the edge permanently missing even after the target
    showed up under the exact right title, since nothing ever re-checked
    the earlier chapter's content again."""
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    a = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "A", "content": "See [[B]]"}).json()

    graph = client.get("/api/graph").json()
    assert not any(e["source"] == a["id"] and e["kind"] == "wiki_link" for e in graph["edges"])

    b = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "B"}).json()

    graph = client.get("/api/graph").json()
    assert any(e["source"] == a["id"] and e["target"] == b["id"] and e["kind"] == "wiki_link" for e in graph["edges"])


def test_wiki_link_edge_appears_once_target_is_renamed_to_match(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    a = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "A", "content": "See [[Renamed]]"}).json()
    b = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Original Title"}).json()

    graph = client.get("/api/graph").json()
    assert not any(e["source"] == a["id"] and e["kind"] == "wiki_link" for e in graph["edges"])

    client.patch(f"/api/notebooks/chapters/{b['id']}", json={"title": "Renamed"})

    graph = client.get("/api/graph").json()
    assert any(e["source"] == a["id"] and e["target"] == b["id"] and e["kind"] == "wiki_link" for e in graph["edges"])


def test_backfill_does_not_duplicate_an_already_correct_link(client):
    """If A already links to B by the same title, creating another
    chapter that happens to match some *other* unresolved link shouldn't
    touch A's existing, already-correct link to B."""
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    b = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "B"}).json()
    a = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "A", "content": "[[B]]"}).json()

    graph = client.get("/api/graph").json()
    wiki_edges = [e for e in graph["edges"] if e["kind"] == "wiki_link"]
    assert len(wiki_edges) == 1
    assert wiki_edges[0]["source"] == a["id"] and wiki_edges[0]["target"] == b["id"]
