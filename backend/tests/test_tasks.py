def test_create_task_defaults(client):
    task = client.post("/api/tasks", json={"title": "Do the thing"}).json()
    assert task["status"] == "todo"
    assert task["priority"] == "medium"
    assert task["repeat_rule"] == "none"


def test_task_linked_to_project(client):
    proj = client.post("/api/projects", json={"title": "Proj"}).json()
    task = client.post("/api/tasks", json={"title": "T", "project_id": proj["id"]}).json()

    proj_tasks = client.get(f"/api/projects/{proj['id']}/tasks").json()
    assert any(t["id"] == task["id"] for t in proj_tasks)


def test_completing_task_awards_xp_by_priority(client):
    urgent = client.post("/api/tasks", json={"title": "U", "priority": "urgent"}).json()
    low = client.post("/api/tasks", json={"title": "L", "priority": "low"}).json()

    urgent_result = client.post(f"/api/tasks/{urgent['id']}/complete").json()
    low_result = client.post(f"/api/tasks/{low['id']}/complete").json()

    assert urgent_result["gamification"]["xp_awarded"] > low_result["gamification"]["xp_awarded"]


def test_cannot_complete_already_completed_task(client):
    task = client.post("/api/tasks", json={"title": "T"}).json()
    client.post(f"/api/tasks/{task['id']}/complete")
    resp = client.post(f"/api/tasks/{task['id']}/complete")
    assert resp.status_code == 400


def test_first_completion_awards_first_steps_badge(client):
    task = client.post("/api/tasks", json={"title": "T"}).json()
    result = client.post(f"/api/tasks/{task['id']}/complete").json()
    assert "First Steps" in result["gamification"]["newly_awarded_badges"]


def test_recurring_task_spawns_next_occurrence_on_completion(client):
    task = client.post(
        "/api/tasks", json={"title": "Standup", "repeat_rule": "daily", "due_at": "2026-07-19T00:00:00Z"}
    ).json()

    client.post(f"/api/tasks/{task['id']}/complete")

    all_tasks = client.get("/api/tasks").json()
    next_occurrences = [t for t in all_tasks if t["title"] == "Standup" and t["status"] == "todo"]
    assert len(next_occurrences) == 1
    assert next_occurrences[0]["due_at"].startswith("2026-07-20")


def test_non_recurring_task_does_not_spawn_next(client):
    task = client.post("/api/tasks", json={"title": "One-off"}).json()
    client.post(f"/api/tasks/{task['id']}/complete")

    all_tasks = client.get("/api/tasks").json()
    todo_matches = [t for t in all_tasks if t["title"] == "One-off" and t["status"] == "todo"]
    assert len(todo_matches) == 0


def test_subtask_lifecycle(client):
    task = client.post("/api/tasks", json={"title": "T"}).json()
    sub = client.post(f"/api/tasks/{task['id']}/subtasks", json={"title": "step 1"}).json()
    assert sub["done"] is False

    toggled = client.patch(f"/api/tasks/subtasks/{sub['id']}", json={"done": True}).json()
    assert toggled["done"] is True

    client.delete(f"/api/tasks/subtasks/{sub['id']}")
    remaining = client.get(f"/api/tasks/{task['id']}/subtasks").json()
    assert remaining == []


def test_delete_then_trash_then_restore_task(client):
    task = client.post("/api/tasks", json={"title": "T"}).json()
    client.delete(f"/api/tasks/{task['id']}")

    assert task["id"] not in [t["id"] for t in client.get("/api/tasks").json()]
    trash = client.get("/api/trash").json()
    assert any(t["type"] == "task" and t["id"] == task["id"] for t in trash)

    client.post(f"/api/trash/task/{task['id']}/restore")
    assert task["id"] in [t["id"] for t in client.get("/api/tasks").json()]


def test_list_tasks_sorts_by_real_priority_severity_not_alphabetically(client):
    # Regression test: native enum columns sort alphabetically in SQL
    # ("high" > "low" alphabetically puts it in the wrong place relative
    # to "medium" and "urgent"). Create in an order that would expose
    # alphabetical sorting if it crept back in.
    client.post("/api/tasks", json={"title": "M", "priority": "medium"})
    client.post("/api/tasks", json={"title": "L", "priority": "low"})
    client.post("/api/tasks", json={"title": "H", "priority": "high"})
    client.post("/api/tasks", json={"title": "U", "priority": "urgent"})

    titles_in_order = [t["title"] for t in client.get("/api/tasks").json()]
    assert titles_in_order == ["U", "H", "M", "L"]


def test_project_task_list_surfaces_active_work_before_done(client):
    proj = client.post("/api/projects", json={"title": "P"}).json()
    done_task = client.post("/api/tasks", json={"title": "Finished", "project_id": proj["id"]}).json()
    client.post(f"/api/tasks/{done_task['id']}/complete")
    client.post("/api/tasks", json={"title": "Still todo", "project_id": proj["id"]})

    titles_in_order = [t["title"] for t in client.get(f"/api/projects/{proj['id']}/tasks").json()]
    assert titles_in_order == ["Still todo", "Finished"]


def test_overdue_task_gets_penalized_when_list_endpoint_is_hit(client):
    # Give the user some XP first -- penalty XP is clamped at 0, so testing
    # from a 0 baseline can't observe a decrease.
    cushion = client.post("/api/tasks", json={"title": "Cushion", "priority": "urgent"}).json()
    client.post(f"/api/tasks/{cushion['id']}/complete")

    task = client.post(
        "/api/tasks", json={"title": "Overdue", "priority": "medium", "due_at": "2020-01-01T00:00:00Z"}
    ).json()
    assert task["is_penalized"] is False

    profile_before = client.get("/api/gamification/profile").json()

    tasks = client.get("/api/tasks").json()
    penalized = next(t for t in tasks if t["id"] == task["id"])
    assert penalized["is_penalized"] is True

    profile_after = client.get("/api/gamification/profile").json()
    assert profile_after["level"]["current_xp"] < profile_before["level"]["current_xp"]


def test_overdue_task_only_penalized_once(client):
    task = client.post(
        "/api/tasks", json={"title": "Overdue", "due_at": "2020-01-01T00:00:00Z"}
    ).json()
    client.get("/api/tasks")  # first check -- applies the penalty
    xp_after_first = client.get("/api/gamification/profile").json()["level"]["current_xp"]

    client.get("/api/tasks")  # second check -- should be a no-op
    xp_after_second = client.get("/api/gamification/profile").json()["level"]["current_xp"]

    assert xp_after_first == xp_after_second


def test_future_and_done_tasks_are_never_penalized(client):
    future = client.post("/api/tasks", json={"title": "Future", "due_at": "2099-01-01T00:00:00Z"}).json()
    no_due_date = client.post("/api/tasks", json={"title": "No due date"}).json()
    done = client.post("/api/tasks", json={"title": "Done", "due_at": "2020-01-01T00:00:00Z"}).json()
    client.post(f"/api/tasks/{done['id']}/complete")

    tasks_by_id = {t["id"]: t for t in client.get("/api/tasks").json()}
    assert tasks_by_id[future["id"]]["is_penalized"] is False
    assert tasks_by_id[no_due_date["id"]]["is_penalized"] is False
    assert tasks_by_id[done["id"]]["is_penalized"] is False
