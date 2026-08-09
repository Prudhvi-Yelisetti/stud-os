"""
Provider abstraction + AI settings + suggestions endpoints. No real API
keys or network calls to Anthropic/OpenAI/Gemini here -- monkeypatch
fakes the key (for the "configured" checks) and the actual chat() call
(for the suggestions endpoint), so this suite runs the same with or
without real credentials in the environment.
"""
from backend.ai.providers.base import ProviderError


def test_every_openai_compatible_preset_constructs_a_client(monkeypatch):
    """Catches typos in a preset's env_key/base_url before they ship --
    each new hosted provider (DeepSeek, Mistral, xAI, Perplexity, ...)
    should construct cleanly given its own key set, same as the
    long-standing ones."""
    from backend.ai.providers.openai_compatible import OpenAICompatibleProvider
    from backend.ai.providers.registry import PROVIDER_PRESETS

    for preset in PROVIDER_PRESETS:
        if preset.kind != "openai_compatible":
            continue
        if preset.requires_key:
            monkeypatch.setenv(preset.env_key, "test-key")
        provider = OpenAICompatibleProvider(preset)
        assert provider._model == preset.default_model
        if preset.base_url:
            assert provider._base_url == preset.base_url
        if preset.requires_key:
            monkeypatch.delenv(preset.env_key)


def test_list_providers_includes_all_presets(client):
    providers = client.get("/api/ai/providers").json()
    keys = {p["key"] for p in providers}
    assert {
        "anthropic", "gemini", "openai", "openrouter", "groq", "nvidia_nim",
        "deepseek", "mistral", "xai", "perplexity", "ollama", "lmstudio",
    } <= keys
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
    assert resp == {
        "feature": "suggestions", "provider_key": None, "model_override": None,
        "effective_provider_key": None,  # no per-feature override AND no global default set
    }


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


def test_feature_without_override_inherits_the_global_default(client, monkeypatch):
    """'default' is just another AISettings row (feature='default') --
    setting it should make an otherwise-untouched feature report that
    provider as its effective_provider_key, without ever writing
    anything into that feature's own row."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/default", json={"provider_key": "anthropic"})

    resp = client.get("/api/ai/settings/suggestions").json()
    assert resp["provider_key"] is None  # no explicit override was ever set
    assert resp["effective_provider_key"] == "anthropic"  # inherited from default


def test_feature_override_wins_over_the_global_default(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client.put("/api/ai/settings/default", json={"provider_key": "anthropic"})
    client.put("/api/ai/settings/study", json={"provider_key": "gemini"})

    study = client.get("/api/ai/settings/study").json()
    assert study["provider_key"] == "gemini"
    assert study["effective_provider_key"] == "gemini"

    # A feature that never set its own override still inherits the default.
    ask = client.get("/api/ai/settings/ask").json()
    assert ask["provider_key"] is None
    assert ask["effective_provider_key"] == "anthropic"


def test_changing_the_default_updates_features_that_never_overrode_it(client, monkeypatch):
    """Confirms the fallback is resolved live at read time, not snapshotted
    when the default was first set -- a feature that inherits should track
    later changes to the default automatically."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    client.put("/api/ai/settings/default", json={"provider_key": "anthropic"})
    assert client.get("/api/ai/settings/suggestions").json()["effective_provider_key"] == "anthropic"

    client.put("/api/ai/settings/default", json={"provider_key": "gemini"})
    assert client.get("/api/ai/settings/suggestions").json()["effective_provider_key"] == "gemini"


def test_removing_a_key_falls_through_instead_of_resolving_to_a_dead_provider(client, monkeypatch):
    """Real bug caught during live testing: Settings' 'Remove' button
    clears a provider's key from .env, but nothing clears the stored
    provider_key on any AISettings row that named it -- an override or
    default naming a now-unconfigured provider must fall through to the
    next thing (default, then None), not be reported as the effective
    provider and fail at call time."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")  # doesn't matter, ollama never needs a key
    client.put("/api/ai/settings/default", json={"provider_key": "anthropic"})
    client.put("/api/ai/settings/study", json={"provider_key": "ollama"})

    # Remove the key -- same as clicking "Remove" in Settings.
    client.put("/api/ai/providers/anthropic/key", json={"api_key": ""})

    default_row = client.get("/api/ai/settings/default").json()
    assert default_row["provider_key"] == "anthropic"  # still stored...
    assert default_row["effective_provider_key"] is None  # ...but not usable anymore

    suggestions = client.get("/api/ai/settings/suggestions").json()
    assert suggestions["effective_provider_key"] is None  # inherited a dead default -> None, not "anthropic"

    # A feature with its own override to a DIFFERENT, still-configured
    # provider is unaffected by the dead default.
    study = client.get("/api/ai/settings/study").json()
    assert study["effective_provider_key"] == "ollama"


def test_task_suggestions_uses_the_global_default_when_no_override_set(client, monkeypatch):
    """The actual usage endpoint (not just GET /settings) has to resolve
    the default too -- this is the part that would have silently kept
    calling nothing if _resolve_provider() weren't wired into it."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/default", json={"provider_key": "anthropic"})
    client.post("/api/tasks", json={"title": "Write the docs"})

    def fake_chat(self, messages, system=None, max_tokens=None):
        return "Focus on writing the docs."

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.get("/api/ai/suggestions/tasks").json()
    assert resp["configured"] is True
    assert resp["suggestion"] == "Focus on writing the docs."


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
