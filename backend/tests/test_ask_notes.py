"""
Ask-your-notes RAG chat. No real API calls -- monkeypatch fakes the
provider's chat() reply, same pattern as the other AI feature tests.
"""


def _seed(client):
    nb_cs = client.post("/api/notebooks", json={"title": "Computer Science"}).json()
    nb_cooking = client.post("/api/notebooks", json={"title": "Cooking"}).json()
    recursion = client.post(
        f"/api/notebooks/{nb_cs['id']}/chapters",
        json={"title": "Recursion", "content": "A function that calls itself to solve smaller subproblems, with a base case to stop it."},
    ).json()
    bread = client.post(
        f"/api/notebooks/{nb_cooking['id']}/chapters",
        json={"title": "Baking Bread", "content": "Preheat the oven and knead the dough before letting it rise."},
    ).json()
    entry = client.post(
        "/api/journal",
        json={"title": "Reflections", "content": "Today I thought about recursive functions and how elegant they are.", "mood": "good", "entry_date": "2026-07-19"},
    ).json()
    return {"nb_cs": nb_cs, "nb_cooking": nb_cooking, "recursion": recursion, "bread": bread, "entry": entry}


def test_ask_not_configured_by_default(client):
    _seed(client)
    resp = client.post("/api/ai/ask", json={"messages": [{"role": "user", "content": "What is recursion?"}]}).json()
    assert resp == {"configured": False, "answer": None, "sources": []}


def test_ask_requires_messages_ending_in_user(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/ask", json={"provider_key": "anthropic"})

    resp = client.post("/api/ai/ask", json={"messages": []})
    assert resp.status_code == 400

    resp = client.post("/api/ai/ask", json={"messages": [{"role": "assistant", "content": "hi"}]})
    assert resp.status_code == 400


def test_ask_retrieves_relevant_context_and_returns_sources(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/ask", json={"provider_key": "anthropic"})
    seeded = _seed(client)

    captured = {}

    def fake_chat(self, messages, system=None):
        captured["system"] = system
        captured["messages"] = messages
        return "Recursion is when a function calls itself."

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post("/api/ai/ask", json={
        "messages": [{"role": "user", "content": "What is recursion?"}],
    }).json()

    assert resp["configured"] is True
    assert resp["answer"] == "Recursion is when a function calls itself."
    source_ids = [s["id"] for s in resp["sources"]]
    # With only 3 chunks total in this test corpus, "top 6" returns
    # everything -- what should actually differ is the ranking: the
    # recursion chapter (a direct match) should rank ahead of the
    # unrelated baking chapter.
    assert source_ids.index(seeded["recursion"]["id"]) < source_ids.index(seeded["bread"]["id"])
    assert "Recursion" in captured["system"]


def test_ask_scoped_to_selected_notebook_excludes_others(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/ask", json={"provider_key": "anthropic"})
    seeded = _seed(client)

    def fake_chat(self, messages, system=None):
        return "answer"

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post("/api/ai/ask", json={
        "messages": [{"role": "user", "content": "Tell me about baking"}],
        "sources": [seeded["nb_cooking"]["id"]],
    }).json()

    source_ids = {s["id"] for s in resp["sources"]}
    assert source_ids <= {seeded["bread"]["id"]}
    assert seeded["recursion"]["id"] not in source_ids
    assert seeded["entry"]["id"] not in source_ids


def test_ask_journal_sentinel_scopes_to_journal_only(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/ask", json={"provider_key": "anthropic"})
    seeded = _seed(client)

    def fake_chat(self, messages, system=None):
        return "answer"

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post("/api/ai/ask", json={
        "messages": [{"role": "user", "content": "What did I reflect on?"}],
        "sources": ["journal"],
    }).json()

    source_ids = {s["id"] for s in resp["sources"]}
    assert source_ids <= {seeded["entry"]["id"]}
    assert seeded["recursion"]["id"] not in source_ids


def test_ask_caps_history_sent_to_provider(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/ask", json={"provider_key": "anthropic"})
    _seed(client)

    long_history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"} for i in range(20)]
    long_history.append({"role": "user", "content": "final question"})

    captured = {}

    def fake_chat(self, messages, system=None):
        captured["messages"] = messages
        return "ok"

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    client.post("/api/ai/ask", json={"messages": long_history})
    assert len(captured["messages"]) == 8
    assert captured["messages"][-1]["content"] == "final question"


def test_ask_surfaces_provider_error_as_502(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/ask", json={"provider_key": "anthropic"})
    _seed(client)

    from backend.ai.providers.base import ProviderError

    def fake_chat(self, messages, system=None):
        raise ProviderError("boom")

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post("/api/ai/ask", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 502


def test_ask_works_with_no_notes_at_all(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/ask", json={"provider_key": "anthropic"})

    def fake_chat(self, messages, system=None):
        assert "No matching notes" in system
        return "I don't have any notes to draw from yet."

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post("/api/ai/ask", json={"messages": [{"role": "user", "content": "hi"}]}).json()
    assert resp["configured"] is True
    assert resp["sources"] == []
