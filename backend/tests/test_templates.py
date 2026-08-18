"""
Integration tests for templates (is_template flag, listing, creating a
chapter from one) and daily notes (get-or-create today, seeded from the
designated daily template).
"""


def test_new_chapter_is_not_a_template_by_default(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "C"}).json()
    assert ch["is_template"] is False
    assert ch["is_daily_template"] is False


def test_marking_a_chapter_as_template_makes_it_listed(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Meeting Template"}).json()
    client.patch(f"/api/notebooks/chapters/{ch['id']}", json={"is_template": True})

    templates = client.get("/api/notebooks/chapters/templates").json()
    assert any(t["id"] == ch["id"] for t in templates)


def test_untemplated_chapters_are_not_listed_as_templates(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Regular note"})
    assert client.get("/api/notebooks/chapters/templates").json() == []


def test_create_from_template_interpolates_placeholders(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    template = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "Log {{date}}", "content": "Started at {{time}}."},
    ).json()
    client.patch(f"/api/notebooks/chapters/{template['id']}", json={"is_template": True})

    created = client.post(f"/api/notebooks/{nb['id']}/chapters/from-template/{template['id']}").json()
    assert "{{date}}" not in created["title"]
    assert "{{time}}" not in created["content"]
    assert "Log " in created["title"]
    assert "Started at " in created["content"]
    # the template itself is untouched
    assert client.get(f"/api/notebooks/chapters/{template['id']}").json()["title"] == "Log {{date}}"


def test_create_from_non_template_chapter_is_rejected(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Not a template"}).json()
    resp = client.post(f"/api/notebooks/{nb['id']}/chapters/from-template/{ch['id']}")
    assert resp.status_code == 400


def test_setting_daily_template_unsets_any_previous_one(client):
    nb = client.post("/api/notebooks", json={"title": "NB"}).json()
    first = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "First"}).json()
    second = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Second"}).json()

    client.patch(f"/api/notebooks/chapters/{first['id']}", json={"is_daily_template": True})
    assert client.get(f"/api/notebooks/chapters/{first['id']}").json()["is_daily_template"] is True

    client.patch(f"/api/notebooks/chapters/{second['id']}", json={"is_daily_template": True})
    assert client.get(f"/api/notebooks/chapters/{first['id']}").json()["is_daily_template"] is False
    assert client.get(f"/api/notebooks/chapters/{second['id']}").json()["is_daily_template"] is True


def test_daily_note_creates_notebook_and_chapter_on_first_call(client):
    assert client.get("/api/notebooks").json() == []

    ch = client.post("/api/daily-notes/today").json()
    notebooks = client.get("/api/notebooks").json()
    assert len(notebooks) == 1
    assert notebooks[0]["title"] == "Daily Notes"
    assert ch["notebook_id"] == notebooks[0]["id"]

    from datetime import date
    assert ch["title"] == date.today().isoformat()


def test_daily_note_is_idempotent_same_day(client):
    first = client.post("/api/daily-notes/today").json()
    second = client.post("/api/daily-notes/today").json()
    assert first["id"] == second["id"]
    # only one notebook, only one chapter in it
    assert len(client.get("/api/notebooks").json()) == 1


def test_daily_note_seeded_from_daily_template(client):
    nb = client.post("/api/notebooks", json={"title": "Templates"}).json()
    template = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "Daily Template", "content": "## Tasks\n## Notes for {{date}}"},
    ).json()
    client.patch(f"/api/notebooks/chapters/{template['id']}", json={"is_daily_template": True})

    today = client.post("/api/daily-notes/today").json()
    assert "## Tasks" in today["content"]
    assert "{{date}}" not in today["content"]


def test_daily_note_without_template_has_empty_content(client):
    today = client.post("/api/daily-notes/today").json()
    assert today["content"] == ""
