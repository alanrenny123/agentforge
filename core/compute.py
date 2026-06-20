"""0G Compute integration via Router API (OpenAI-compatible)."""

import os
import json
from openai import OpenAI


def get_client(api_key: str = None) -> OpenAI:
    """Create an OpenAI client pointed at 0G Compute Router.
    
    If api_key is provided, use it (per-user key). Otherwise fall back to env var.
    """
    return OpenAI(
        base_url=os.getenv("OG_COMPUTE_BASE_URL", "https://router-api.0g.ai/v1"),
        api_key=api_key or os.getenv("OG_COMPUTE_API_KEY", ""),
    )


def list_models() -> list[dict]:
    """List available models on 0G Compute."""
    client = get_client()
    models = client.models.list()
    return [{"id": m.id, "owned_by": getattr(m, "owned_by", "unknown")} for m in models.data]


def chat_completion(
    system_prompt: str,
    user_message: str,
    model: str = "zai-org/GLM-5-FP8",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    api_key: str = None,
) -> str:
    """Send a chat completion request to 0G Compute."""
    client = get_client(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
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
    model: str = "zai-org/GLM-5-FP8",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    api_key: str = None,
):
    """Stream a chat completion response from 0G Compute."""
    client = get_client(api_key=api_key)
    stream = client.chat.completions.create(
        model=model,
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


def test_connection() -> dict:
    """Test connectivity to 0G Compute Router."""
    try:
        client = get_client()
        models = client.models.list()
        return {
            "status": "connected",
            "endpoint": os.getenv("OG_COMPUTE_BASE_URL"),
            "models_available": len(models.data),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
