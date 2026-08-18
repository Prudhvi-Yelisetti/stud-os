"""
Integration tests for the tags feature: inline #tags and frontmatter
properties across chapters and journal entries, the GET /api/tags and
GET /api/tags/{tag} endpoints, and cleanup on trash.
"""


def test_chapter_out_exposes_inline_tags(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "C", "content": "this is about #algorithms and #review"},
    ).json()
    assert ch["tags"] == ["algorithms", "review"]


def test_chapter_out_exposes_frontmatter_properties_and_tags(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    content = "---\nstatus: draft\ntags:\n  - fm-tag\n---\n\nbody text #inline-tag"
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": content}).json()
    assert ch["properties"] == {"status": "draft", "tags": ["fm-tag"]}
    assert ch["tags"] == ["fm-tag", "inline-tag"]


def test_tags_appear_in_global_tag_list_with_counts(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "A", "content": "#shared #only-a"})
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "B", "content": "#shared"})

    tags = {t["name"]: t["count"] for t in client.get("/api/tags").json()}
    assert tags["shared"] == 2
    assert tags["only-a"] == 1


def test_get_tagged_items_returns_matching_chapters(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "A", "content": "#findme"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "B", "content": "no tag here"})

    items = client.get("/api/tags/findme").json()
    assert len(items) == 1
    assert items[0]["id"] == ch["id"]
    assert items[0]["type"] == "chapter"


def test_get_tagged_items_unknown_tag_returns_empty(client):
    assert client.get("/api/tags/does-not-exist").json() == []


def test_editing_content_updates_tags(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": "#old"}).json()
    assert client.get("/api/tags/old").json() != []

    client.patch(f"/api/notebooks/chapters/{ch['id']}", json={"content": "#new"})
    assert client.get("/api/tags/old").json() == []
    assert len(client.get("/api/tags/new").json()) == 1


def test_restoring_a_version_resyncs_tags(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": "#original"}).json()
    client.patch(f"/api/notebooks/chapters/{ch['id']}", json={"content": "#changed"})
    assert client.get("/api/tags/original").json() == []

    versions = client.get(f"/api/notebooks/chapters/{ch['id']}/versions").json()
    old_version = next(v for v in versions if v["content_snapshot"] == "#original")
    client.post(f"/api/notebooks/chapters/{ch['id']}/versions/{old_version['id']}/restore")

    assert len(client.get("/api/tags/original").json()) == 1


def test_updating_properties_endpoint_rewrites_frontmatter_and_tags(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": "body only"}).json()
    assert ch["properties"] == {}

    updated = client.patch(
        f"/api/notebooks/chapters/{ch['id']}/properties",
        json={"properties": {"status": "done", "tags": ["done-tag"]}},
    ).json()
    assert updated["properties"] == {"status": "done", "tags": ["done-tag"]}
    assert "body only" in updated["content"]  # body preserved
    assert updated["tags"] == ["done-tag"]
    assert len(client.get("/api/tags/done-tag").json()) == 1

    # a version snapshot was taken -- properties edits go through the same
    # history mechanism as any other content edit
    versions = client.get(f"/api/notebooks/chapters/{ch['id']}/versions").json()
    assert any(v["content_snapshot"] == "body only" for v in versions)


def test_permanently_deleting_chapter_removes_its_tag_links(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": "#temp"}).json()
    assert client.get("/api/tags/temp").json() != []

    client.delete(f"/api/notebooks/chapters/{ch['id']}")  # soft delete (trash)
    client.delete(f"/api/trash/chapter/{ch['id']}")  # permanent delete

    assert client.get("/api/tags/temp").json() == []
    assert client.get("/api/tags").json() == []


def test_deleting_notebook_cascades_tag_cleanup_for_its_chapters(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C", "content": "#cascadetag"})

    client.delete(f"/api/notebooks/{nb['id']}")  # soft delete notebook (chapters implicitly hidden)
    client.delete(f"/api/trash/notebook/{nb['id']}")  # permanent delete

    assert client.get("/api/tags/cascadetag").json() == []


def test_journal_entry_tags_and_properties_work_the_same_way(client):
    entry = client.post(
        "/api/journal",
        json={"title": "Today", "content": "---\nmood-note: good\n---\n\nfelt #productive", "entry_date": "2026-08-16"},
    ).json()
    assert entry["properties"] == {"mood-note": "good"}
    assert entry["tags"] == ["productive"]

    items = client.get("/api/tags/productive").json()
    assert len(items) == 1
    assert items[0]["type"] == "journal"
    assert items[0]["id"] == entry["id"]


def test_journal_entry_properties_endpoint(client):
    entry = client.post("/api/journal", json={"title": "E", "content": "body", "entry_date": "2026-08-16"}).json()
    updated = client.patch(f"/api/journal/{entry['id']}/properties", json={"properties": {"mood-note": "ok"}}).json()
    assert updated["properties"] == {"mood-note": "ok"}
    assert "body" in updated["content"]


def test_permanently_deleting_journal_entry_removes_tag_links(client):
    entry = client.post("/api/journal", json={"title": "E", "content": "#jtag", "entry_date": "2026-08-16"}).json()
    assert client.get("/api/tags/jtag").json() != []

    client.delete(f"/api/journal/{entry['id']}")
    client.delete(f"/api/trash/journal/{entry['id']}")

    assert client.get("/api/tags/jtag").json() == []
