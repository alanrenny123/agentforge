"""Multi-provider AI Compute integration via OpenAI-compatible APIs.

Supported providers:
  - 0G Compute (default)
  - OpenRouter
  - OpenAI
  - Anthropic
  - Any OpenAI-compatible endpoint (custom)
"""

import os
from openai import OpenAI


# ─── Provider Registry ────────────────────────────────────────────────────────

PROVIDERS = {
    "0g": {
        "name": "0G Compute",
        "base_url": "https://router-api.0g.ai/v1",
        "default_model": "zai-org/GLM-5-FP8",
        "icon": "⛓️",
    },
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-4o-mini",
        "icon": "🔀",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "icon": "🟢",
    },
    "anthropic": {
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com/v1/",
        "default_model": "claude-sonnet-4-20250514",
        "icon": "🟠",
    },
    "custom": {
        "name": "Custom (OpenAI-compatible)",
        "base_url": "",
        "default_model": "",
        "icon": "🔧",
    },
}


def get_client(api_key: str = None, provider: str = "0g", base_url: str = None) -> OpenAI:
    """Create an OpenAI client for the specified provider.

    All providers use the OpenAI SDK since they expose OpenAI-compatible APIs.
    """
    prov = PROVIDERS.get(provider, PROVIDERS["0g"])
    url = base_url or prov["base_url"]
    key = api_key or os.getenv("OG_COMPUTE_API_KEY", "")
    return OpenAI(base_url=url, api_key=key)


def list_providers() -> list[dict]:
    """Return available providers (safe to send to frontend)."""
    return [
        {"id": pid, "name": p["name"], "icon": p["icon"], "default_model": p["default_model"]}
        for pid, p in PROVIDERS.items()
    ]


def list_models(provider: str = "0g", api_key: str = None) -> list[dict]:
    """List available models for a provider."""
    client = get_client(api_key=api_key, provider=provider)
    models = client.models.list()
    return [{"id": m.id, "owned_by": getattr(m, "owned_by", "unknown")} for m in models.data]


def chat_completion(
    system_prompt: str,
    user_message: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    api_key: str = None,
    provider: str = "0g",
    base_url: str = None,
) -> str:
    """Send a chat completion request to the specified provider."""
    prov = PROVIDERS.get(provider, PROVIDERS["0g"])
    resolved_model = model or prov["default_model"]
    client = get_client(api_key=api_key, provider=provider, base_url=base_url)
    response = client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def chat_completion_streaming(
    system_prompt: str,
    user_message: str,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    api_key: str = None,
    provider: str = "0g",
    base_url: str = None,
):
    """Stream a chat completion response from the specified provider."""
    prov = PROVIDERS.get(provider, PROVIDERS["0g"])
    resolved_model = model or prov["default_model"]
    client = get_client(api_key=api_key, provider=provider, base_url=base_url)
    stream = client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def test_connection(provider: str = "0g", api_key: str = None) -> dict:
    """Test connectivity to a provider."""
    prov = PROVIDERS.get(provider, PROVIDERS["0g"])
    if not api_key:
        return {
            "status": "ready",
            "message": f"{prov['name']} is available. Enter your API key to start chatting.",
            "endpoint": prov["base_url"],
        }
    try:
        client = get_client(api_key=api_key, provider=provider)
        models = client.models.list()
        return {
            "status": "connected",
            "endpoint": prov["base_url"],
            "models_available": len(models.data),
        }
    except Exception as e:
        error_msg = str(e)
        if "402" in error_msg or "insufficient_balance" in error_msg:
            return {
                "status": "ready",
                "message": f"{prov['name']} is available. Your API key needs credits.",
                "endpoint": prov["base_url"],
            }
        return {"status": "error", "error": error_msg}
