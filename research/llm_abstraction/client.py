"""DeepSeek OpenAI-compatible client. Never logs secrets."""
from __future__ import annotations

import hashlib
import time
from typing import Any, Optional

from research.llm_abstraction.config import BASE_URL, CONFIG_ID, ProposerConfig
from research.llm_abstraction.secrets import load_api_key, sanitize

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


def _usage(resp) -> dict[str, Any]:
    u = getattr(resp, "usage", None)
    if u is None:
        return {}
    details = getattr(u, "completion_tokens_details", None)
    reasoning = getattr(details, "reasoning_tokens", None) if details else None
    return {
        "prompt_tokens": getattr(u, "prompt_tokens", None),
        "completion_tokens": getattr(u, "completion_tokens", None),
        "total_tokens": getattr(u, "total_tokens", None),
        "reasoning_tokens": reasoning,
        "cached_tokens": getattr(
            getattr(u, "prompt_tokens_details", None), "cached_tokens", None
        ),
    }


def chat_complete(messages: list[dict], config: Optional[ProposerConfig] = None) -> dict:
    config = config or ProposerConfig()
    if OpenAI is None:
        return sanitize({
            "blocked": True, "error": "NO_OPENAI_PACKAGE", "content": "",
            "model": config.model, "config_id": CONFIG_ID,
        })
    try:
        api_key = load_api_key()
    except RuntimeError:
        return sanitize({
            "blocked": True, "error": "NO_API_KEY", "content": "",
            "model": config.model, "config_id": CONFIG_ID,
        })
    client = OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
        timeout=config.timeout_s,
    )
    last_err = None
    attempts = 1 + max(0, int(config.retries_network))
    for attempt in range(attempts):
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=config.model,
                messages=messages,
                max_tokens=config.max_tokens,
                reasoning_effort=config.reasoning_effort,
                response_format={"type": "json_object"},
                extra_body={"thinking": {"type": config.thinking_type}},
            )
            latency = time.time() - t0
            msg = resp.choices[0].message
            content = msg.content or ""
            reasoning = (
                getattr(msg, "reasoning_content", None)
                or getattr(msg, "reasoning", None)
                or ""
            )
            if not isinstance(reasoning, str):
                reasoning = str(reasoning)
            rec = {
                "blocked": False,
                "error": None,
                "content": content,
                "reasoning_len": len(reasoning),
                "reasoning_sha": hashlib.sha256(reasoning.encode()).hexdigest()[:16]
                if reasoning else None,
                "reasoning_tail": reasoning[-500:] if reasoning else "",
                "usage": _usage(resp),
                "latency_s": round(latency, 3),
                "request_id": getattr(resp, "id", None),
                "model": getattr(resp, "model", None) or config.model,
                "attempt": attempt,
                "config_id": CONFIG_ID,
            }
            return sanitize(rec)
        except Exception as exc:
            last_err = f"{type(exc).__name__}"
            time.sleep(min(2 ** attempt, 8))
    return sanitize({
        "blocked": True,
        "error": last_err or "API_ERROR",
        "content": "",
        "model": config.model,
        "config_id": CONFIG_ID,
    })
