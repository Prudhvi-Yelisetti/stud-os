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


def test_search_tag_operator_filters_to_tagged_chapters(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    tagged = client.post(
        f"/api/notebooks/{nb['id']}/chapters", json={"title": "Tagged", "content": "About cars. #vehicles"}
    ).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Untagged", "content": "About cars too."})

    results = client.get("/api/search", params={"q": "tag:vehicles"}).json()
    ids = {r["id"] for r in results}
    assert ids == {tagged["id"]}


def test_search_exclude_tag_operator(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Archived", "content": "old #archived"})
    active = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Active", "content": "old stuff"}).json()

    results = client.get("/api/search", params={"q": "-tag:archived old"}).json()
    ids = {r["id"] for r in results if r["type"] == "chapter"}
    assert ids == {active["id"]}


def test_search_notebook_operator_scopes_to_one_notebook(client):
    work = client.post("/api/notebooks", json={"title": "Work"}).json()
    home = client.post("/api/notebooks", json={"title": "Home"}).json()
    work_ch = client.post(f"/api/notebooks/{work['id']}/chapters", json={"title": "Budget"}).json()
    client.post(f"/api/notebooks/{home['id']}/chapters", json={"title": "Budget"})

    results = client.get("/api/search", params={"q": "notebook:Work budget"}).json()
    ids = {r["id"] for r in results}
    assert ids == {work_ch["id"]}


def test_search_exclude_word_operator(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Draft plan", "content": "still a draft"})
    final = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Final plan"}).json()

    results = client.get("/api/search", params={"q": "plan -draft"}).json()
    ids = {r["id"] for r in results if r["type"] == "chapter"}
    assert ids == {final["id"]}


def test_search_tag_operator_also_matches_journal_entries(client):
    entry = client.post(
        "/api/journal", json={"title": "Gym day", "entry_date": "2026-07-19", "content": "leg day #fitness"}
    ).json()
    client.post("/api/journal", json={"title": "Rest day", "entry_date": "2026-07-20", "content": "no gym"})

    results = client.get("/api/search", params={"q": "tag:fitness"}).json()
    ids = {r["id"] for r in results if r["type"] == "journal"}
    assert ids == {entry["id"]}
