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


class AIProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict], system: str | None = None) -> str:
        """Send a chat completion request and return the model's reply
        as plain text. `messages` is [{"role": "user"|"assistant", "content": str}, ...].
        Raises ProviderError on failure."""
