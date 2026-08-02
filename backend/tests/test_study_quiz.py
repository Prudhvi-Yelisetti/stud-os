"""
Study-coach quiz generation. No real API calls -- monkeypatch fakes the
provider's chat() reply, same pattern as test_ai_providers.py's task
suggestion tests.
"""
import json

_VALID_QUIZ_REPLY = json.dumps({
    "questions": [
        {
            "question": "What does recursion require to terminate?",
            "choices": ["A loop counter", "A base case", "A global variable", "A return type"],
            "correct_index": 1,
            "explanation": "Without a base case, a recursive function calls itself forever.",
        },
    ]
})


def _seed_chapter(client, content="A function that calls itself to solve smaller subproblems, with a base case."):
    nb = client.post("/api/notebooks", json={"title": "CS"}).json()
    return client.post(f"/api/notebooks/{nb['id']}/chapters", json={"title": "Recursion", "content": content}).json()


def test_quiz_not_configured_by_default(client):
    ch = _seed_chapter(client)
    resp = client.post(f"/api/ai/study/quiz/{ch['id']}").json()
    assert resp == {"configured": False, "questions": []}


def test_quiz_requires_content(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/study", json={"provider_key": "anthropic"})
    ch = _seed_chapter(client, content="")

    resp = client.post(f"/api/ai/study/quiz/{ch['id']}")
    assert resp.status_code == 400


def test_quiz_404_for_missing_chapter(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/study", json={"provider_key": "anthropic"})

    resp = client.post("/api/ai/study/quiz/does-not-exist")
    assert resp.status_code == 404


def test_quiz_generates_and_parses_questions(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/study", json={"provider_key": "anthropic"})
    ch = _seed_chapter(client)

    def fake_chat(self, messages, system=None):
        assert "Recursion" in messages[0]["content"]
        return _VALID_QUIZ_REPLY

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post(f"/api/ai/study/quiz/{ch['id']}").json()
    assert resp["configured"] is True
    assert len(resp["questions"]) == 1
    q = resp["questions"][0]
    assert q["correct_index"] == 1
    assert len(q["choices"]) == 4


def test_quiz_tolerates_markdown_fenced_json(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/study", json={"provider_key": "anthropic"})
    ch = _seed_chapter(client)

    def fake_chat(self, messages, system=None):
        return f"```json\n{_VALID_QUIZ_REPLY}\n```"

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post(f"/api/ai/study/quiz/{ch['id']}").json()
    assert len(resp["questions"]) == 1


def test_quiz_surfaces_malformed_response_as_502(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/study", json={"provider_key": "anthropic"})
    ch = _seed_chapter(client)

    def fake_chat(self, messages, system=None):
        return "not valid json at all"

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post(f"/api/ai/study/quiz/{ch['id']}")
    assert resp.status_code == 502


def test_quiz_rejects_out_of_range_correct_index(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client.put("/api/ai/settings/study", json={"provider_key": "anthropic"})
    ch = _seed_chapter(client)

    bad_reply = json.dumps({"questions": [{
        "question": "?", "choices": ["a", "b"], "correct_index": 9, "explanation": "e",
    }]})

    def fake_chat(self, messages, system=None):
        return bad_reply

    monkeypatch.setattr("backend.ai.providers.anthropic_provider.AnthropicProvider.chat", fake_chat)

    resp = client.post(f"/api/ai/study/quiz/{ch['id']}")
    assert resp.status_code == 502
