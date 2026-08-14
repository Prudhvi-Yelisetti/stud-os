import os

from backend.ai.providers.base import AIProvider, DEFAULT_MAX_TOKENS, ProviderError, friendly_error
from backend.ai.providers.registry import ProviderPreset


class GeminiProvider(AIProvider):
    def __init__(self, preset: ProviderPreset):
        self._preset = preset
        self._model = os.environ.get(preset.model_env_key, preset.default_model)
        api_key = os.environ.get(preset.env_key)
        if not api_key:
            raise ProviderError(f"{preset.env_key} is not set")
        self._api_key = api_key

    def list_models(self) -> list[str]:
        try:
            from google import genai
        except ImportError as e:
            raise ProviderError("google-genai package is not installed") from e

        try:
            client = genai.Client(api_key=self._api_key)
            # Names come back as "models/gemini-2.5-flash" -- stripped to
            # match the bare form generate_content() and this preset's
            # own default_model/GEMINI_MODEL already use.
            return [m.name.removeprefix("models/") for m in client.models.list()]
        except Exception as e:
            raise ProviderError(friendly_error("Gemini", e)) from e

    def chat(
        self, messages: list[dict], system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS, model: str | None = None,
    ) -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ProviderError("google-genai package is not installed") from e

        try:
            client = genai.Client(api_key=self._api_key)
            contents = [
                types.Content(
                    role="model" if m["role"] == "assistant" else "user",
                    parts=[types.Part.from_text(text=m["content"])],
                )
                for m in messages
            ]
            config = types.GenerateContentConfig(
                system_instruction=system if system else None,
                max_output_tokens=max_tokens,
            )
            response = client.models.generate_content(model=model or self._model, contents=contents, config=config)
            return response.text or ""
        except Exception as e:
            raise ProviderError(friendly_error("Gemini", e)) from e
