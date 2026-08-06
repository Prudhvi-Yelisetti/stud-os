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
    base_url_env_key: str | None = None  # env var to override base_url -- for local servers on a
    # non-default host/port (Docker, LAN machine, custom port), not just the model
    requires_key: bool = True  # False for local servers (Ollama, LM Studio) that don't check a key at
    # all -- for these, "configured" means "the base URL is set to something", not "a real secret exists"


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
    ProviderPreset(
        key="ollama", label="Ollama (local)", kind="openai_compatible",
        env_key="OLLAMA_API_KEY", model_env_key="OLLAMA_MODEL",
        default_model="llama3.1",
        base_url="http://localhost:11434/v1", base_url_env_key="OLLAMA_BASE_URL",
        requires_key=False,
    ),
    ProviderPreset(
        key="lmstudio", label="LM Studio (local)", kind="openai_compatible",
        env_key="LMSTUDIO_API_KEY", model_env_key="LMSTUDIO_MODEL",
        default_model="local-model",
        base_url="http://localhost:1234/v1", base_url_env_key="LMSTUDIO_BASE_URL",
        requires_key=False,
    ),
]

_BY_KEY = {p.key: p for p in PROVIDER_PRESETS}


def get_preset(key: str) -> ProviderPreset | None:
    return _BY_KEY.get(key)
