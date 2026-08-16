"""Lightweight OpenAI-compatible chat completion helper (no SDK required).

RecRedTeam talks to chat models through a single, dependency-free helper so
that real-agent adapters and the optional judge channel share one code path.

Configuration (standard user-oriented variables, never agent runtime vars):

- ``USER_LLM_API_KEY``   API key (required to enable LLM calls)
- ``USER_LLM_BASE_URL``  OpenAI-compatible base URL (default: api.openai.com)
- ``USER_LLM_MODEL``     model name (default: gpt-4o-mini)
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Optional

_API_KEY_ENV = "USER_LLM_API_KEY"
_BASE_URL_ENV = "USER_LLM_BASE_URL"
_MODEL_ENV = "USER_LLM_MODEL"


def is_configured() -> bool:
    """True when an API key is present in the environment."""
    return bool(os.environ.get(_API_KEY_ENV))


def chat_complete(
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
    timeout: int = 30,
    response_format: Optional[dict] = None,
) -> Optional[str]:
    """Run a chat completion and return the assistant text.

    Returns ``None`` when no API key is configured, the call fails, or the
    response cannot be parsed -- callers should fall back to deterministic
    behavior in that case.
    """
    api_key = os.environ.get(_API_KEY_ENV)
    if not api_key:
        return None
    base_url = os.environ.get(_BASE_URL_ENV, "https://api.openai.com/v1")
    model = os.environ.get(_MODEL_ENV, "gpt-4o-mini")

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None
