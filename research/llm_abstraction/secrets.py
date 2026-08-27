"""Load DeepSeek credentials without ever logging them."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SECRET_ENV = "DEEPSEEK_API_KEY"
_KEY_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
_SECRET_KEY_NAMES = {
    "api_key", "apikey", "authorization", "auth", "token",
    "secret", "password", "DEEPSEEK_API_KEY", "deepseek_api_key",
    "bearer", "x-api-key",
}


def load_api_key() -> str:
    """Return the key from env or gitignored .env. Never print it."""
    raw = os.environ.get(SECRET_ENV)
    if raw:
        return raw.strip().strip("'").strip('"')
    path = ROOT / ".env"
    if not path.is_file():
        raise RuntimeError("DEEPSEEK_API_KEY missing (env and .env)")
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == SECRET_ENV:
            return v.strip().strip("'").strip('"')
    raise RuntimeError("DEEPSEEK_API_KEY missing in .env")


def key_present() -> bool:
    try:
        return len(load_api_key()) >= 20
    except RuntimeError:
        return False


def key_length() -> int:
    try:
        return len(load_api_key())
    except RuntimeError:
        return 0


def redact_text(text: str) -> str:
    if not text:
        return text
    out = _KEY_RE.sub("sk-[REDACTED]", text)
    # belt: env-style assignments
    out = re.sub(
        rf"{SECRET_ENV}\s*=\s*\S+",
        f"{SECRET_ENV}=REDACTED",
        out,
    )
    out = re.sub(
        r"(Bearer\s+)[A-Za-z0-9_\-]+",
        r"\1REDACTED",
        out,
        flags=re.I,
    )
    return out


def sanitize(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k) in _SECRET_KEY_NAMES or str(k).lower() in _SECRET_KEY_NAMES:
                out[k] = "REDACTED"
            else:
                out[k] = sanitize(v)
        return out
    if isinstance(obj, list):
        return [sanitize(x) for x in obj]
    if isinstance(obj, str):
        return redact_text(obj)
    return obj
