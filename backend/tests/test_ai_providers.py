"""
Provider abstraction + AI settings + suggestions endpoints. No real API
keys or network calls to Anthropic/OpenAI/Gemini here -- monkeypatch
fakes the key (for the "configured" checks) and the actual chat() call
(for the suggestions endpoint), so this suite runs the same with or
without real credentials in the environment.
"""
from backend.ai.providers.base import ProviderError


def test_list_providers_includes_all_presets(client):
    providers = client.get("/api/ai/providers").json()
    keys = {p["key"] for p in providers}
    assert {"anthropic", "gemini", "openai", "openrouter", "groq", "nvidia_nim", "ollama", "lmstudio"} <= keys
    assert all("configured" in p and "label" in p for p in providers)


def test_local_providers_are_always_configured_without_a_key(client):
    """Ollama/LM Studio don't check a key at all -- unlike every other
    preset, they should show as usable with nothing set in .env."""
    providers = {p["key"]: p for p in client.get("/api/ai/providers").json()}
    assert providers["ollama"]["configured"] is True
    assert providers["lmstudio"]["configured"] is True


def test_local_provider_can_be_selected_with_no_api_key_set(client):
    resp = client.put("/api/ai/settings/suggestions", json={"provider_key": "ollama"})
    assert resp.status_code == 200
    assert resp.json()["provider_key"] == "ollama"


def test_local_provider_respects_base_url_override(monkeypatch):
    """OLLAMA_BASE_URL should win over the built-in default -- e.g. Ollama
    running in Docker or on another machine on the LAN, not localhost."""
    from backend.ai.providers.openai_compatible import OpenAICompatibleProvider
    from backend.ai.providers.registry import get_preset

    monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.50:11434/v1")
    provider = OpenAICompatibleProvider(get_preset("ollama"))
    assert provider._base_url == "http://192.168.1.50:11434/v1"
    assert provider._api_key == "not-needed"  # never checked by Ollama, but the SDK needs a non-empty string


def test_settings_default_is_unconfigured(client):
    resp = client.get("/api/ai/settings/suggestions").json()
    assert resp == {"feature": "suggestions", "provider_key": None, "model_override": None}


def test_settings_rejects_provider_with_no_key_set(client):
    resp = client.put("/api/ai/settings/suggestions", json={"provider_key": "anthropic"})
    assert resp.status_code == 400


def test_settings_accepts_and_persists_configured_provider(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    resp = client.put("/api/ai/settings/suggestions", json={"provider_key": "anthropic"})
    assert resp.status_code == 200
    assert resp.json()["provider_key"] == "anthropic"

    persisted = client.get("/api/ai/settings/suggestions").json()
    assert persisted["provider_key"] == "anthropic"


def test_settings_can_be_cleared(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/suggestions", json={"provider_key": "anthropic"})
    resp = client.put("/api/ai/settings/suggestions", json={"provider_key": None})
    assert resp.json()["provider_key"] is None


def test_related_notes_excludes_self_and_ranks_by_relevance(client):
    nb = client.post("/api/notebooks", json={"title": "CS"}).json()
    recursion = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "Recursion", "content": "A function calling itself to solve smaller subproblems, with a base case."},
    ).json()
    iteration = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "Iteration", "content": "Using for and while loops to repeat a block of code until a condition is met."},
    ).json()
    baking = client.post(
        f"/api/notebooks/{nb['id']}/chapters",
        json={"title": "Baking Bread", "content": "Preheat the oven and knead the dough before letting it rise."},
    ).json()

    results = client.get(f"/api/ai/suggestions/related/{recursion['id']}").json()
    ids = [r["id"] for r in results]

    assert recursion["id"] not in ids
    assert iteration["id"] in ids
    assert ids.index(iteration["id"]) < ids.index(baking["id"])


def test_related_notes_empty_for_chapter_with_no_content(client):
    nb = client.post("/api/notebooks", json={"title": "Empty"}).json()
    ch = client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Blank", "content": ""}).json()
    assert client.get(f"/api/ai/suggestions/related/{ch['id']}").json() == []


def test_task_suggestions_not_configured_by_default(client):
    resp = client.get("/api/ai/suggestions/tasks").json()
    assert resp == {"configured": False, "suggestion": None}


def test_task_suggestions_with_no_open_tasks(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/suggestions", json={"provider_key": "anthropic"})

    resp = client.get("/api/ai/suggestions/tasks").json()
    assert resp["configured"] is True
    assert "no open tasks" in resp["suggestion"].lower()


def test_task_suggestions_calls_configured_provider(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/suggestions", json={"provider_key": "anthropic"})
    client.post("/api/tasks", json={"title": "Write the report", "priority": "high"})

    def fake_chat(self, messages, system=None):
        assert "Write the report" in messages[0]["content"]
        return "Focus on the report first -- it's your only high-priority item."

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.get("/api/ai/suggestions/tasks").json()
    assert resp["configured"] is True
    assert "report" in resp["suggestion"].lower()


def test_task_suggestions_surfaces_provider_error_as_502(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/suggestions", json={"provider_key": "anthropic"})
    client.post("/api/tasks", json={"title": "Something", "priority": "medium"})

    def fake_chat(self, messages, system=None):
        raise ProviderError("simulated failure")

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.get("/api/ai/suggestions/tasks")
    assert resp.status_code == 502
