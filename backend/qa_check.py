"""
End-to-end smoke test against a running backend (localhost:8420).
Exercises the full feature surface with real HTTP calls -- not a
substitute for unit tests, but catches integration regressions cheaply.

Usage:
    uv pip install --python .venv/bin/python requests   # one-time
    .venv/bin/python backend/qa_check.py                # backend must be running
"""
import requests, sys, json
from datetime import datetime, timedelta, timezone

B = "http://localhost:8420/api"
results = []

def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), "-", name, ("" if cond else f"  ({detail})"))

# --- Notes ---
nb = requests.post(f"{B}/notebooks", json={"title":"QA Notebook"}).json()
check("create notebook", "id" in nb)
ch1 = requests.post(f"{B}/notebooks/{nb['id']}/chapters", json={"title":"Alpha","content":"first"}).json()
ch2 = requests.post(f"{B}/notebooks/{nb['id']}/chapters", json={"title":"Beta","content":"links to [[Alpha]]"}).json()
backlinks = requests.get(f"{B}/notebooks/chapters/{ch1['id']}/backlinks").json()
check("wiki-link creates backlink", any(b["id"]==ch2["id"] for b in backlinks), backlinks)
upd = requests.patch(f"{B}/notebooks/chapters/{ch1['id']}", json={"content":"first v2"}).json()
check("chapter version bumps on edit", upd["version"] == 2, upd["version"])

# --- Projects + Tasks + Gamification + Subtasks + Recurrence ---
proj = requests.post(f"{B}/projects", json={"title":"QA Project"}).json()
task = requests.post(f"{B}/tasks", json={"title":"QA Task","priority":"high","project_id":proj["id"],"repeat_rule":"daily"}).json()
proj_tasks = requests.get(f"{B}/projects/{proj['id']}/tasks").json()
check("task linked to project", any(t["id"]==task["id"] for t in proj_tasks))

sub = requests.post(f"{B}/tasks/{task['id']}/subtasks", json={"title":"sub1"}).json()
check("create subtask", "id" in sub)
sub_upd = requests.patch(f"{B}/tasks/subtasks/{sub['id']}", json={"done": True}).json()
check("toggle subtask done", sub_upd["done"] is True)

profile_before = requests.get(f"{B}/gamification/profile").json()
complete = requests.post(f"{B}/tasks/{task['id']}/complete").json()
check("task completion awards XP", complete["gamification"]["xp_awarded"] == 20, complete["gamification"])
profile_after = requests.get(f"{B}/gamification/profile").json()
check("XP actually persisted", profile_after["level"]["current_xp"] > profile_before["level"]["current_xp"])

all_tasks = requests.get(f"{B}/tasks").json()
recurred = [t for t in all_tasks if t["title"]=="QA Task" and t["status"]=="todo"]
check("recurring task spawned next occurrence", len(recurred) == 1, len(recurred))

# --- Journal ---
entry = requests.post(f"{B}/journal", json={"title":"QA Entry","content":"testing","mood":"good","entry_date":"2026-07-19"}).json()
check("create journal entry", "id" in entry)
entry_upd = requests.patch(f"{B}/journal/{entry['id']}", json={"title":"QA Entry edited"}).json()
check("edit journal entry", entry_upd["title"] == "QA Entry edited")

# --- Search ---
search_results = requests.get(f"{B}/search", params={"q":"QA"}).json()
types_found = {r["type"] for r in search_results}
check("search finds across types", {"chapter","task","journal","notebook","project"} & types_found == {"chapter","task","journal"} or len(types_found) >= 3, types_found)

# --- Graph ---
graph = requests.get(f"{B}/graph").json()
check("graph has nodes", len(graph["nodes"]) > 0, len(graph["nodes"]))
check("graph has wiki_link edge", any(e["kind"]=="wiki_link" for e in graph["edges"]))

# --- Attachments ---
files = {"file": ("qa.txt", b"qa content", "text/plain")}
att = requests.post(f"{B}/attachments", params={"owner_type":"chapter","owner_id":ch1["id"]}, files=files).json()
check("upload attachment", "id" in att)
dl = requests.get(f"{B}/attachments/{att['id']}/download")
check("download attachment", dl.status_code == 200 and dl.content == b"qa content")

# --- Trash / Restore / Permanent delete ---
requests.delete(f"{B}/notebooks/{nb['id']}")  # trashes notebook (and should hide its chapters from normal views)
trash = requests.get(f"{B}/trash").json()
check("deleted notebook appears in trash", any(t["type"]=="notebook" and t["id"]==nb["id"] for t in trash), trash)

nb_after_delete = requests.get(f"{B}/notebooks").json()
check("trashed notebook hidden from normal list", not any(n["id"]==nb["id"] for n in nb_after_delete))

restore = requests.post(f"{B}/trash/notebook/{nb['id']}/restore").json()
check("restore notebook", restore["trashed_at"] is None)
nb_after_restore = requests.get(f"{B}/notebooks").json()
check("restored notebook reappears", any(n["id"]==nb["id"] for n in nb_after_restore))

requests.delete(f"{B}/notebooks/{nb['id']}")
purge = requests.delete(f"{B}/trash/notebook/{nb['id']}")
check("permanent delete returns 204", purge.status_code == 204, purge.status_code)
trash_after_purge = requests.get(f"{B}/trash").json()
check("permanently deleted item gone from trash", not any(t["id"]==nb["id"] for t in trash_after_purge))

# --- Summary ---
failed = [r for r in results if not r[1]]
print(f"\n{len(results)-len(failed)}/{len(results)} passed")
if failed:
    print("FAILURES:", [f[0] for f in failed])
    sys.exit(1)
