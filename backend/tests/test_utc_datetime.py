"""
Real bug, found by reading base.py and confirmed live before fixing:
DateTime(timezone=True) on SQLite silently drops tzinfo on read despite
the flag. That's not just a Python-level footgun (comparing the result
to an aware datetime raises TypeError) -- it meant every timestamp got
serialized to the API response with no UTC marker at all
("2026-08-14T01:00:00" instead of "...+00:00"/"...Z"), and a marker-less
ISO string is parsed by JS `new Date(...)` as LOCAL time, not UTC. Due
dates and "overdue" highlighting were silently wrong by the browser's
UTC offset for anyone not physically in UTC.

Everything here goes through the real HTTP API (create a task, read the
response), same as the rest of this suite -- that's also just a more
honest test of the actual bug, which was specifically about what the
API sends the frontend, not an internal detail.
"""
from datetime import datetime, timezone


def _has_utc_marker(iso_string: str) -> bool:
    return iso_string.endswith("Z") or iso_string.endswith("+00:00")


def test_task_response_serializes_due_at_with_an_explicit_utc_marker(client):
    """The end-to-end shape that actually matters: the JSON the frontend
    receives must carry a timezone marker, or `new Date(...)` in the
    browser silently misparses it as local time."""
    resp = client.post("/api/tasks", json={"title": "t", "due_at": "2026-08-14T01:00:00+00:00"}).json()
    assert resp["due_at"] is not None
    assert _has_utc_marker(resp["due_at"]), f"no UTC marker in serialized due_at: {resp['due_at']!r}"


def test_due_at_value_is_preserved_exactly_through_the_round_trip(client):
    """Not just present, but correct -- confirms this isn't dropping or
    shifting the actual instant, only fixing the marker."""
    sent = "2026-08-14T01:00:00+00:00"
    resp = client.post("/api/tasks", json={"title": "t", "due_at": sent}).json()
    assert datetime.fromisoformat(resp["due_at"].replace("Z", "+00:00")) == datetime.fromisoformat(sent)


def test_created_at_also_serializes_with_an_explicit_utc_marker(client):
    """TimestampedMixin's created_at/updated_at affect every table, not
    just tasks -- confirmed on a completely different resource so this
    isn't accidentally only true for Task specifically."""
    resp = client.post("/api/notebooks", json={"title": "NB"}).json()
    assert _has_utc_marker(resp["created_at"])
    assert _has_utc_marker(resp["updated_at"])


def test_a_task_naively_sent_without_a_timezone_still_round_trips_with_a_utc_marker(client):
    """Defensive case: even a client that sends a timezone-less datetime
    string (arguably its own bug) shouldn't come back from this API
    ambiguous -- this app treats every datetime as UTC by convention, so
    a naive input is stored and returned as UTC, not silently naive."""
    resp = client.post("/api/tasks", json={"title": "t", "due_at": "2026-08-14T01:00:00"}).json()
    assert _has_utc_marker(resp["due_at"])


def test_overdue_penalty_still_correctly_detects_a_genuinely_overdue_task(client):
    """The one place this bug's underlying naive-vs-aware mismatch could
    have broken something server-side, not just in the browser: the
    lazy overdue-penalty check's DB query. Confirms it still finds a
    task that's actually overdue after the UTCDateTime change."""
    from datetime import timedelta
    past_due = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    task = client.post("/api/tasks", json={"title": "overdue me", "due_at": past_due}).json()

    tasks = client.get("/api/tasks").json()  # triggers the lazy overdue check
    found = next(t for t in tasks if t["id"] == task["id"])
    assert found["is_penalized"] is True
