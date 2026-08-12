"""
Common interface every chat-completion provider implements. Kept
deliberately minimal -- one method -- so adding a provider is cheap and
callers don't need to know which concrete backend they're talking to.
"""
from abc import ABC, abstractmethod


class ProviderError(Exception):
    """Raised when a provider call fails (bad/missing key, API error,
    network issue, etc). Callers catch this and surface a clean message
    rather than a raw SDK traceback."""


# Default cap on the model's reply length. 1024 sounds generous but isn't --
# a 10-question quiz (question + 4 choices + explanation each, wrapped in
# JSON) runs well past it and gets cut off mid-object, which then fails to
# parse as JSON and surfaces as a confusing "could not generate a valid
# quiz" error rather than an obviously-a-length-problem one. Callers that
# know they need more (or less) room pass their own max_tokens.
DEFAULT_MAX_TOKENS = 4096


class AIProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], system: str | None = None, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        """Send a chat completion request and return the model's reply
        as plain text. `messages` is [{"role": "user"|"assistant", "content": str}, ...].
        Raises ProviderError on failure."""

    @abstractmethod
    def verify(self) -> None:
        """Confirms this provider is actually reachable and, for keyed
        providers, that the key is genuinely valid -- not just present as
        a non-empty string (which is all `is_configured()` checks, since
        that's meant to run with no API call at all). Deliberately a
        models-list call, not a chat completion: cheap or free on every
        provider this app supports, and doesn't risk running a real
        generation against a possibly-slow local model just to answer
        "is this connected". Returns normally on success, raises
        ProviderError with a clear message on failure."""
