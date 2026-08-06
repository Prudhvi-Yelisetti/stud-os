"""
Turns a registry preset into a live AIProvider instance, and answers
"is this one usable right now" for the settings UI (no API call made --
just checks whether the expected env var is set).
"""
import os

from backend.ai.providers.base import AIProvider, ProviderError
from backend.ai.providers.registry import PROVIDER_PRESETS, get_preset
from backend.ai.providers.anthropic_provider import AnthropicProvider
from backend.ai.providers.gemini_provider import GeminiProvider
from backend.ai.providers.openai_compatible import OpenAICompatibleProvider

_ADAPTERS = {
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "openai_compatible": OpenAICompatibleProvider,
}


def is_configured(provider_key: str) -> bool:
    preset = get_preset(provider_key)
    if preset is None:
        return False
    if not preset.requires_key:
        # Local servers (Ollama, LM Studio) don't check a key at all -- there's
        # nothing to "configure" beyond having the server running, which we
        # don't probe for here (same "no API call made" rule as the rest of
        # this function). If it's not actually running, the request just
        # fails at call time with a clear connection-refused error instead.
        return True
    return bool(os.environ.get(preset.env_key))


def list_providers_with_status() -> list[dict]:
    return [
        {"key": p.key, "label": p.label, "configured": is_configured(p.key)}
        for p in PROVIDER_PRESETS
    ]


def get_provider(provider_key: str) -> AIProvider:
    preset = get_preset(provider_key)
    if preset is None:
        raise ProviderError(f"Unknown provider: {provider_key}")
    adapter_cls = _ADAPTERS.get(preset.kind)
    if adapter_cls is None:
        raise ProviderError(f"No adapter registered for kind: {preset.kind}")
    return adapter_cls(preset)
