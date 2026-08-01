"""
Known provider presets. Each entry describes how to reach one provider --
adding a new OpenAI-compatible service later (say, Together or DeepSeek)
is a new dict here, not new code. `kind` picks which adapter class in
factory.py handles it.

Model names drift over time and this is an open-source project other
people will run long after this was written, so every preset's default
model is overridable via its own env var rather than hardcoded as gospel
-- see .env.example.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    key: str
    label: str
    kind: str  # "anthropic" | "gemini" | "openai_compatible"
    env_key: str  # env var holding the API key
    model_env_key: str  # env var to override the default model
    default_model: str
    base_url: str | None = None  # only used by kind="openai_compatible"; None = provider's own default


PROVIDER_PRESETS: list[ProviderPreset] = [
    ProviderPreset(
        key="anthropic", label="Anthropic (Claude)", kind="anthropic",
        env_key="ANTHROPIC_API_KEY", model_env_key="ANTHROPIC_MODEL",
        default_model="claude-sonnet-4-6",
    ),
    ProviderPreset(
        key="gemini", label="Google Gemini", kind="gemini",
        env_key="GEMINI_API_KEY", model_env_key="GEMINI_MODEL",
        default_model="gemini-2.5-flash",
    ),
    ProviderPreset(
        key="openai", label="OpenAI", kind="openai_compatible",
        env_key="OPENAI_API_KEY", model_env_key="OPENAI_MODEL",
        default_model="gpt-4o-mini", base_url=None,
    ),
    ProviderPreset(
        key="openrouter", label="OpenRouter", kind="openai_compatible",
        env_key="OPENROUTER_API_KEY", model_env_key="OPENROUTER_MODEL",
        default_model="meta-llama/llama-3.3-70b-instruct",
        base_url="https://openrouter.ai/api/v1",
    ),
    ProviderPreset(
        key="groq", label="Groq", kind="openai_compatible",
        env_key="GROQ_API_KEY", model_env_key="GROQ_MODEL",
        default_model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
    ),
    ProviderPreset(
        key="nvidia_nim", label="NVIDIA NIM", kind="openai_compatible",
        env_key="NVIDIA_API_KEY", model_env_key="NVIDIA_MODEL",
        default_model="meta/llama-3.3-70b-instruct",
        base_url="https://integrate.api.nvidia.com/v1",
    ),
]

_BY_KEY = {p.key: p for p in PROVIDER_PRESETS}


def get_preset(key: str) -> ProviderPreset | None:
    return _BY_KEY.get(key)
