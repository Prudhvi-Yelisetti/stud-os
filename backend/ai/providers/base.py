"""
Common interface every chat-completion provider implements. Kept
deliberately minimal so adding a provider is cheap and callers don't
need to know which concrete backend they're talking to.
"""
from abc import ABC, abstractmethod
import re


class ProviderError(Exception):
    """Raised when a provider call fails (bad/missing key, API error,
    network issue, etc). Callers catch this and surface a clean message
    rather than a raw SDK traceback."""


def friendly_error(label: str, exc: Exception) -> str:
    """Turns an SDK exception into a short, human-readable message
    instead of a raw repr full of request IDs and nested dicts -- e.g.
    "Error code: 401 - {'type': 'error', 'error': {'type':
    'authentication_error', 'message': 'invalid x-api-key'}, ...}"
    becomes "the API key was rejected -- double check it's correct and
    hasn't been revoked." Best-effort and intentionally not exhaustive
    across every SDK's exception hierarchy: falls back to extracting
    just the human 'message' field from a dict-shaped body, and failing
    that, a trimmed version of str(exc), rather than the raw thing."""
    status = getattr(exc, "status_code", None)
    text = str(exc)
    lowered = text.lower()

    if status in (401, 403) or "authentication" in lowered or "invalid api key" in lowered or "invalid x-api-key" in lowered:
        return f"{label}: the API key was rejected -- double check it's correct and hasn't been revoked."
    if status == 429 or "rate limit" in lowered:
        return f"{label}: rate limited -- try again in a moment."
    if "connection" in type(exc).__name__.lower() or ("connect" in lowered and "refused" in lowered) or "timed out" in lowered:
        return f"{label}: couldn't reach the server -- check it's running and reachable."

    match = re.search(r"'message':\s*'([^']+)'", text)
    if match:
        return f"{label}: {match.group(1)}"

    if len(text) > 160:
        text = text[:160].rsplit(" ", 1)[0] + "…"
    return f"{label}: {text}"


# Default cap on the model's reply length. 1024 sounds generous but isn't --
# a 10-question quiz (question + 4 choices + explanation each, wrapped in
# JSON) runs well past it and gets cut off mid-object, which then fails to
# parse as JSON and surfaces as a confusing "could not generate a valid
# quiz" error rather than an obviously-a-length-problem one. Callers that
# know they need more (or less) room pass their own max_tokens.
DEFAULT_MAX_TOKENS = 4096


class AIProvider(ABC):
    @abstractmethod
    def chat(
        self, messages: list[dict], system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS, model: str | None = None,
    ) -> str:
        """Send a chat completion request and return the model's reply
        as plain text. `messages` is [{"role": "user"|"assistant", "content": str}, ...].
        `model`, if given, overrides the provider's configured default
        for just this call (see routers/ai.py's model resolution).
        Raises ProviderError on failure."""

    @abstractmethod
    def list_models(self) -> list[str]:
        """Returns the real, live list of model IDs this provider
        currently offers -- what Settings' "add a model" flow shows to
        choose from. Raises ProviderError on failure (bad key, offline
        server, etc)."""

    def verify(self) -> None:
        """Confirms this provider is actually reachable and, for keyed
        providers, that the key is genuinely valid -- not just present as
        a non-empty string (which is all `is_configured()` checks, since
        that's meant to run with no API call at all). Built on
        list_models() rather than its own separate call: same cheap,
        free-or-near-free models-list request either way, and it means
        "is this connected" and "what models does it offer" can never
        disagree with each other about whether the provider is reachable.
        Returns normally on success, raises ProviderError on failure."""
        self.list_models()
