"""
Covers AIModel CRUD (Settings' "add a model" flow) and _resolve_model()'s
cascade: a feature's own model_override wins, else the resolved
provider's default added model, else None (let the adapter fall back to
its own env-var/preset default -- unchanged pre-model-management
behavior). No real API keys or network calls -- available-models
fetching is tested via a monkeypatched list_models(), same pattern as
chat() elsewhere in this suite.
"""
from backend.ai.providers.base import ProviderError


def test_available_models_returns_live_list_from_the_provider(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def fake_list_models(self):
        return ["claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"]

    monkeypatch.setattr(
        "backend.ai.providers.anthropic_provider.AnthropicProvider.list_models", fake_list_models
    )

    resp = client.get("/api/ai/providers/anthropic/available-models")
    assert resp.status_code == 200
    assert resp.json() == ["claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5"]


def test_available_models_surfaces_provider_error_as_502(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def fake_list_models(self):
        raise ProviderError("Anthropic (Claude): the API key was rejected")

    monkeypatch.setattr(
        "backend.ai.providers.anthropic_provider.AnthropicProvider.list_models", fake_list_models
    )

    resp = client.get("/api/ai/providers/anthropic/available-models")
    assert resp.status_code == 502
    assert "rejected" in resp.json()["detail"]


def test_available_models_404s_for_unknown_provider(client):
    resp = client.get("/api/ai/providers/not-a-real-provider/available-models")
    assert resp.status_code == 404


def test_added_models_starts_empty(client):
    assert client.get("/api/ai/providers/anthropic/models").json() == []


def test_first_added_model_becomes_default_automatically(client):
    resp = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-sonnet-5"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_id"] == "claude-sonnet-5"
    assert body["is_default"] is True


def test_second_added_model_is_not_default(client):
    client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-sonnet-5"})
    resp = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-opus-4-8"})
    assert resp.json()["is_default"] is False

    models = client.get("/api/ai/providers/anthropic/models").json()
    assert len(models) == 2
    assert sum(1 for m in models if m["is_default"]) == 1


def test_adding_the_same_model_twice_is_idempotent(client):
    first = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-sonnet-5"}).json()
    second = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-sonnet-5"}).json()
    assert first["id"] == second["id"]
    assert len(client.get("/api/ai/providers/anthropic/models").json()) == 1


def test_set_default_model_unsets_the_previous_one(client):
    m1 = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-sonnet-5"}).json()
    m2 = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-opus-4-8"}).json()
    assert m1["is_default"] is True and m2["is_default"] is False

    resp = client.put(f"/api/ai/providers/anthropic/models/{m2['id']}/default")
    assert resp.json()["is_default"] is True

    models = {m["id"]: m for m in client.get("/api/ai/providers/anthropic/models").json()}
    assert models[m1["id"]]["is_default"] is False
    assert models[m2["id"]]["is_default"] is True


def test_removing_the_default_model_promotes_another(client):
    m1 = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-sonnet-5"}).json()
    m2 = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-opus-4-8"}).json()
    assert m1["is_default"] is True

    resp = client.delete(f"/api/ai/providers/anthropic/models/{m1['id']}")
    assert resp.status_code == 204

    remaining = client.get("/api/ai/providers/anthropic/models").json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == m2["id"]
    assert remaining[0]["is_default"] is True  # promoted, not left with zero default


def test_removing_the_last_model_leaves_none_default(client):
    m1 = client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-sonnet-5"}).json()
    client.delete(f"/api/ai/providers/anthropic/models/{m1['id']}")
    assert client.get("/api/ai/providers/anthropic/models").json() == []


def test_remove_model_404s_for_unknown_row(client):
    resp = client.delete("/api/ai/providers/anthropic/models/not-a-real-id")
    assert resp.status_code == 404


def test_resolve_model_falls_back_to_provider_default_when_no_feature_override(client, monkeypatch):
    """The actual point of this feature: a feature with no model_override
    of its own should use its resolved provider's default ADDED model,
    not just whatever the provider adapter would fall back to on its
    own -- confirmed by inspecting what model actually reaches chat()."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/default", json={"provider_key": "anthropic"})
    client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-haiku-4-5"})
    client.post("/api/tasks", json={"title": "Write the docs"})

    captured = {}

    def fake_chat(self, messages, system=None, max_tokens=None, model=None):
        captured["model"] = model
        return "Focus on writing the docs."

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.get("/api/ai/suggestions/tasks")
    assert resp.json()["configured"] is True
    assert captured["model"] == "claude-haiku-4-5"


def test_feature_model_override_wins_over_provider_default_model(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/default", json={"provider_key": "anthropic"})
    client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-haiku-4-5"})
    client.put(
        "/api/ai/settings/suggestions",
        json={"provider_key": "anthropic", "model_override": "claude-opus-4-8"},
    )
    client.post("/api/tasks", json={"title": "Write the docs"})

    captured = {}

    def fake_chat(self, messages, system=None, max_tokens=None, model=None):
        captured["model"] = model
        return "Focus on writing the docs."

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    client.get("/api/ai/suggestions/tasks")
    assert captured["model"] == "claude-opus-4-8"  # override, not the provider's added default


def test_ask_accepts_a_per_chat_model_override(client, monkeypatch):
    """The literal 'select a model while chatting' ask -- Ask's endpoint
    takes its own one-off model, separate from whatever the provider's
    default added model is."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/ask", json={"provider_key": "anthropic"})
    client.post("/api/ai/providers/anthropic/models", json={"model_id": "claude-haiku-4-5"})

    captured = {}

    def fake_chat(self, messages, system=None, max_tokens=None, model=None):
        captured["model"] = model
        return "answer"

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post("/api/ai/ask", json={
        "messages": [{"role": "user", "content": "hi"}], "model": "claude-opus-4-8",
    })
    assert resp.json()["model_used"] == "claude-opus-4-8"
    assert captured["model"] == "claude-opus-4-8"


def test_no_added_models_resolves_to_none_not_an_error(client, monkeypatch):
    """No models added for the provider yet -- _resolve_model() should
    quietly resolve to None (adapter's own default kicks in), not error
    or block the feature from working at all."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/default", json={"provider_key": "anthropic"})
    client.post("/api/tasks", json={"title": "Write the docs"})

    captured = {}

    def fake_chat(self, messages, system=None, max_tokens=None, model=None):
        captured["model"] = model
        return "Focus on writing the docs."

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.get("/api/ai/suggestions/tasks")
    assert resp.json()["configured"] is True
    assert captured["model"] is None
