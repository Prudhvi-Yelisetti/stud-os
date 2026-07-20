def test_create_and_edit_journal_entry(client):
    entry = client.post(
        "/api/journal", json={"title": "Day 1", "content": "learned things", "mood": "good", "entry_date": "2026-07-19"}
    ).json()
    assert entry["mood"] == "good"

    updated = client.patch(f"/api/journal/{entry['id']}", json={"title": "Day 1 (edited)"}).json()
    assert updated["title"] == "Day 1 (edited)"
    assert updated["content"] == "learned things"  # untouched fields survive a partial update


def test_journal_entries_sorted_by_date_desc(client):
    client.post("/api/journal", json={"title": "Old", "entry_date": "2026-07-01"})
    client.post("/api/journal", json={"title": "New", "entry_date": "2026-07-19"})

    entries = client.get("/api/journal").json()
    assert entries[0]["title"] == "New"
