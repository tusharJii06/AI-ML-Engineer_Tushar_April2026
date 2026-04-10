from __future__ import annotations

import json
import os
from typing import Any

import httpx


def chat_completion(
    messages: list[dict[str, str]],
    *,
    mock: bool = False,
    temperature: float = 0.2,
) -> str:
    """
    Minimal OpenAI-compatible chat call. When mock=True or no API key, returns a stub
    (orchestrators should still produce structured output from tools).
    """
    if mock:
        return _mock_reply(messages)

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return _mock_reply(messages)

    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    url = f"{base}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            url,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"] or ""


def _mock_reply(messages: list[dict[str, str]]) -> str:
    last = messages[-1]["content"] if messages else ""
    return json.dumps(
        {
            "mock": True,
            "echo_prefix": last[:200],
            "note": "Stub LLM: downstream logic uses tool outputs for decisions.",
        }
    )
