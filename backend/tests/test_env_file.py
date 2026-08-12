"""
Covers backend/ai/env_file.py (the .env upsert helper) and the
PUT /api/ai/providers/{key}/key + POST /api/ai/providers/{key}/verify
endpoints -- the Settings page's "paste your key in here" feature, and
its "Test connection" action.

Every test below sets ENV_FILE_PATH to a tmp_path file via monkeypatch
BEFORE calling anything that might write -- upsert_key() re-resolves the
env file path fresh on every call specifically so this works without
needing to reload/reimport modules, and so nothing in this file can
ever accidentally touch the real repo .env.
"""
from backend.ai.env_file import upsert_key


def test_upsert_adds_a_new_key(tmp_path, monkeypatch):
    env_file = tmp_path / "test.env"
    monkeypatch.setenv("ENV_FILE_PATH", str(env_file))

    upsert_key("SOME_API_KEY", "sk-abc123")

    assert env_file.read_text().strip() == "SOME_API_KEY=sk-abc123"
    assert __import__("os").environ["SOME_API_KEY"] == "sk-abc123"


def test_upsert_replaces_an_existing_key_without_duplicating(tmp_path, monkeypatch):
    env_file = tmp_path / "test.env"
    env_file.write_text("OTHER_KEY=untouched\nSOME_API_KEY=old-value\n")
    monkeypatch.setenv("ENV_FILE_PATH", str(env_file))

    upsert_key("SOME_API_KEY", "new-value")

    lines = env_file.read_text().splitlines()
    assert lines.count("SOME_API_KEY=new-value") == 1
    assert "SOME_API_KEY=old-value" not in lines
    assert "OTHER_KEY=untouched" in lines  # other lines survive untouched


def test_upsert_with_empty_value_removes_the_line(tmp_path, monkeypatch):
    env_file = tmp_path / "test.env"
    env_file.write_text("OTHER_KEY=untouched\nSOME_API_KEY=old-value\n")
    monkeypatch.setenv("ENV_FILE_PATH", str(env_file))
    monkeypatch.setenv("SOME_API_KEY", "old-value")

    upsert_key("SOME_API_KEY", "")

    lines = env_file.read_text().splitlines()
    assert "SOME_API_KEY=old-value" not in lines
    assert not any(line.startswith("SOME_API_KEY=") for line in lines)
    assert "OTHER_KEY=untouched" in lines
    assert "SOME_API_KEY" not in __import__("os").environ


def test_set_provider_key_endpoint_writes_and_reports_configured(client, tmp_path, monkeypatch):
    env_file = tmp_path / "test.env"
    monkeypatch.setenv("ENV_FILE_PATH", str(env_file))
    monkeypatch.setattr(
        "backend.ai.providers.anthropic_provider.AnthropicProvider.verify", lambda self: None
    )

    resp = client.put("/api/ai/providers/anthropic/key", json={"api_key": "sk-test-key"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["key"] == "anthropic"

    # The real env var (ANTHROPIC_API_KEY) is what the rest of the
    # system actually reads, not just this endpoint's own return value.
    assert __import__("os").environ["ANTHROPIC_API_KEY"] == "sk-test-key"
    assert "ANTHROPIC_API_KEY=sk-test-key" in env_file.read_text()

    # Provider list reflects it immediately -- no restart needed.
    providers = {p["key"]: p for p in client.get("/api/ai/providers").json()}
    assert providers["anthropic"]["configured"] is True


def test_set_provider_key_rejects_and_rolls_back_an_unverifiable_key(client, tmp_path, monkeypatch):
    """The actual point of this feature: a key that doesn't really work
    (typo'd, revoked, wrong provider) must not be saved and reported as
    "Configured" -- it should fail loudly right away instead of silently
    sitting there until the first real feature call 502s."""
    env_file = tmp_path / "test.env"
    monkeypatch.setenv("ENV_FILE_PATH", str(env_file))

    def fake_verify(self):
        from backend.ai.providers.base import ProviderError
        raise ProviderError("invalid x-api-key")

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.verify", fake_verify)

    resp = client.put("/api/ai/providers/anthropic/key", json={"api_key": "sk-bad-key"})
    assert resp.status_code == 502
    assert "invalid x-api-key" in resp.json()["detail"]

    # Rolled back completely -- not left half-saved anywhere.
    assert "ANTHROPIC_API_KEY" not in env_file.read_text()
    assert "ANTHROPIC_API_KEY" not in __import__("os").environ
    providers = {p["key"]: p for p in client.get("/api/ai/providers").json()}
    assert providers["anthropic"]["configured"] is False


def test_verify_endpoint_reports_success(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    monkeypatch.setattr(
        "backend.ai.providers.anthropic_provider.AnthropicProvider.verify", lambda self: None
    )

    resp = client.post("/api/ai/providers/anthropic/verify")
    assert resp.status_code == 200
    assert resp.json()["configured"] is True


def test_verify_endpoint_reports_failure_without_touching_env(client, tmp_path, monkeypatch):
    """'Test connection' on an already-connected provider must not
    silently clear or modify the saved key just because the live check
    failed (e.g. a transient network blip, or the key having since been
    revoked) -- it only reports what it found."""
    env_file = tmp_path / "test.env"
    monkeypatch.setenv("ENV_FILE_PATH", str(env_file))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    env_file.write_text("ANTHROPIC_API_KEY=sk-test-key\n")

    def fake_verify(self):
        from backend.ai.providers.base import ProviderError
        raise ProviderError("connection timed out")

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.verify", fake_verify)

    resp = client.post("/api/ai/providers/anthropic/verify")
    assert resp.status_code == 502
    assert "connection timed out" in resp.json()["detail"]
    assert "ANTHROPIC_API_KEY=sk-test-key" in env_file.read_text()  # untouched


def test_verify_endpoint_works_for_local_providers_with_no_key(client, monkeypatch):
    """Directly addresses the real gap this feature exists for: a local
    server (Ollama) reports configured=True unconditionally, with no key
    at all to check -- 'Test connection' has to be able to probe it
    anyway (is it actually running right now), not just keyed providers."""
    def fake_verify(self):
        from backend.ai.providers.base import ProviderError
        raise ProviderError("Connection refused -- is Ollama running?")

    monkeypatch.setattr(
        "backend.ai.providers.openai_compatible.OpenAICompatibleProvider.verify", fake_verify
    )

    resp = client.post("/api/ai/providers/ollama/verify")
    assert resp.status_code == 502
    assert "Ollama running" in resp.json()["detail"]


def test_set_provider_key_endpoint_clears_with_empty_string(client, tmp_path, monkeypatch):
    env_file = tmp_path / "test.env"
    monkeypatch.setenv("ENV_FILE_PATH", str(env_file))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    env_file.write_text("ANTHROPIC_API_KEY=sk-test-key\n")

    resp = client.put("/api/ai/providers/anthropic/key", json={"api_key": ""})
    assert resp.status_code == 200
    assert resp.json()["configured"] is False
    assert "ANTHROPIC_API_KEY" not in env_file.read_text()


def test_set_provider_key_endpoint_404s_for_unknown_provider(client, tmp_path, monkeypatch):
    monkeypatch.setenv("ENV_FILE_PATH", str(tmp_path / "test.env"))
    resp = client.put("/api/ai/providers/not-a-real-provider/key", json={"api_key": "x"})
    assert resp.status_code == 404


def test_response_includes_requires_key_flag(client):
    providers = {p["key"]: p for p in client.get("/api/ai/providers").json()}
    assert providers["anthropic"]["requires_key"] is True
    assert providers["ollama"]["requires_key"] is False
