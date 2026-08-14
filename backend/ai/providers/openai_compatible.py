import os

from backend.ai.providers.base import AIProvider, DEFAULT_MAX_TOKENS, ProviderError, friendly_error
from backend.ai.providers.registry import ProviderPreset


class OpenAICompatibleProvider(AIProvider):
    """One adapter for every service that speaks the OpenAI chat-completions
    schema -- OpenAI itself (base_url=None uses the SDK's default), plus
    OpenRouter/Groq/NVIDIA NIM/etc via their own base_url. This is what
    makes 'add another popular provider' a registry entry, not new code."""

    def __init__(self, preset: ProviderPreset):
        self._preset = preset
        self._model = os.environ.get(preset.model_env_key, preset.default_model)
        self._base_url = (
            os.environ.get(preset.base_url_env_key, preset.base_url) if preset.base_url_env_key else preset.base_url
        )
        api_key = os.environ.get(preset.env_key)
        if not api_key:
            if not preset.requires_key:
                # Local OpenAI-compatible servers (Ollama, LM Studio) don't
                # check the key, but the SDK still requires a non-empty
                # string to construct a client.
                api_key = "not-needed"
            else:
                raise ProviderError(f"{preset.env_key} is not set")
        self._api_key = api_key

    def _client(self):
        from openai import OpenAI
        client_kwargs = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        return OpenAI(**client_kwargs)

    def list_models(self) -> list[str]:
        try:
            from openai import OpenAI  # noqa: F401 -- import check only, _client() does the real import
        except ImportError as e:
            raise ProviderError("openai package is not installed") from e

        try:
            return [m.id for m in self._client().models.list()]
        except Exception as e:
            raise ProviderError(friendly_error(self._preset.label, e)) from e

    def chat(
        self, messages: list[dict], system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS, model: str | None = None,
    ) -> str:
        try:
            from openai import OpenAI  # noqa: F401
        except ImportError as e:
            raise ProviderError("openai package is not installed") from e

        try:
            client = self._client()
            full_messages = ([{"role": "system", "content": system}] if system else []) + messages
            response = client.chat.completions.create(
                model=model or self._model, messages=full_messages, max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ProviderError(friendly_error(self._preset.label, e)) from e
