import os

from backend.ai.providers.base import AIProvider, DEFAULT_MAX_TOKENS, ProviderError
from backend.ai.providers.registry import ProviderPreset


class AnthropicProvider(AIProvider):
    def __init__(self, preset: ProviderPreset):
        self._preset = preset
        self._model = os.environ.get(preset.model_env_key, preset.default_model)
        api_key = os.environ.get(preset.env_key)
        if not api_key:
            raise ProviderError(f"{preset.env_key} is not set")
        self._api_key = api_key

    def verify(self) -> None:
        try:
            import anthropic
        except ImportError as e:
            raise ProviderError("anthropic package is not installed") from e

        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            client.models.list(limit=1)
        except Exception as e:
            raise ProviderError(f"{self._preset.label} rejected the request: {e}") from e

    def chat(self, messages: list[dict], system: str | None = None, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        try:
            import anthropic
        except ImportError as e:
            raise ProviderError("anthropic package is not installed") from e

        try:
            client = anthropic.Anthropic(api_key=self._api_key)
            kwargs = {"model": self._model, "max_tokens": max_tokens, "messages": messages}
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            return "".join(block.text for block in response.content if block.type == "text")
        except Exception as e:
            raise ProviderError(f"Anthropic request failed: {e}") from e
