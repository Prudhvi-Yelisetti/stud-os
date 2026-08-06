import os

from backend.ai.providers.base import AIProvider, DEFAULT_MAX_TOKENS, ProviderError
from backend.ai.providers.registry import ProviderPreset


class OpenAICompatibleProvider(AIProvider):
    """One adapter for every service that speaks the OpenAI chat-completions
    schema -- OpenAI itself (base_url=None uses the SDK's default), plus
    OpenRouter/Groq/NVIDIA NIM/etc via their own base_url. This is what
    makes 'add another popular provider' a registry entry, not new code."""

    def __init__(self, preset: ProviderPreset):
        self._preset = preset
        self._model = os.environ.get(preset.model_env_key, preset.default_model)
        api_key = os.environ.get(preset.env_key)
        if not api_key:
            raise ProviderError(f"{preset.env_key} is not set")
        self._api_key = api_key

    def chat(self, messages: list[dict], system: str | None = None, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ProviderError("openai package is not installed") from e

        try:
            client_kwargs = {"api_key": self._api_key}
            if self._preset.base_url:
                client_kwargs["base_url"] = self._preset.base_url
            client = OpenAI(**client_kwargs)

            full_messages = ([{"role": "system", "content": system}] if system else []) + messages
            response = client.chat.completions.create(
                model=self._model, messages=full_messages, max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ProviderError(f"{self._preset.label} request failed: {e}") from e
