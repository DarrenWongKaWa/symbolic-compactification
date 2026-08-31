"""Small public-output redaction boundary for the research preview.

The release workflow deliberately does not read ``.env`` files, request
objects, authentication headers, or the process environment.  This module is
the second line of defence for the few free-form strings that are allowed to
reach provenance warnings or human-readable report metadata.

It is intentionally conservative: credential-shaped values are replaced with
``[REDACTED]``.  It is not a general data-loss-prevention system, so callers
must still use allow-listed schemas and must never pass raw configuration,
request, environment, or exception objects to persistence APIs.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REDACTED = "[REDACTED]"

_PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----.*?"
    r"-----END (?:[A-Z0-9 ]+ )?PRIVATE KEY-----",
    re.IGNORECASE | re.DOTALL,
)
_AUTH_HEADER_RE = re.compile(
    r"(?im)(\b(?:proxy-)?authorization\s*[:=]\s*)[^\r\n]+"
)
_COOKIE_HEADER_RE = re.compile(
    r"(?im)(\b(?:set-)?cookie\s*:\s*)[^\r\n]+"
)
_BEARER_RE = re.compile(r"(?i)(\bbearer\s+)[^\s,;]+")
_SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"(?i)(\b(?:[A-Z0-9_.-]*(?:api[_-]?key|secret|token|password|passwd|"
    r"private[_-]?key|credential|session[_-]?cookie)[A-Z0-9_.-]*|authorization|"
    r"proxy-authorization|x-api-key)\s*[:=]\s*)"
    r"(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;&\r\n]+)"
)
_URL_USERINFO_RE = re.compile(
    r"(?i)(\b[a-z][a-z0-9+.-]*://)[^\s/@:]+:[^\s/@]+@"
)
_KNOWN_TOKEN_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(
        r"(?:gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,})",
        re.IGNORECASE,
    ),
    re.compile(r"(?:xox[baprs]-[A-Za-z0-9-]{8,}|AKIA[A-Z0-9]{12,})"),
    re.compile(r"AIza[A-Za-z0-9_-]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\."
               r"[A-Za-z0-9_-]{8,}\b"),
)
_SENSITIVE_FIELD_RE = re.compile(
    r"(?i)(?:^|[_\-.])(?:api[_-]?key|secret|token|password|passwd|"
    r"private[_-]?key|credential|authorization|auth[_-]?header|"
    r"session[_-]?cookie)(?:$|[_\-.])"
)


def redact_text(value: str) -> str:
    """Return ``value`` with common credential forms removed.

    Only strings are accepted.  This avoids accidentally calling ``repr`` on
    an exception, request, or client object whose representation may contain
    credentials.
    """
    if not isinstance(value, str):
        raise TypeError("redact_text requires a string")
    redacted = _PRIVATE_KEY_RE.sub(REDACTED, value)
    redacted = _AUTH_HEADER_RE.sub(r"\1" + REDACTED, redacted)
    redacted = _COOKIE_HEADER_RE.sub(r"\1" + REDACTED, redacted)
    redacted = _BEARER_RE.sub(r"\1" + REDACTED, redacted)
    redacted = _SENSITIVE_ASSIGNMENT_RE.sub(r"\1" + REDACTED, redacted)
    redacted = _URL_USERINFO_RE.sub(r"\1" + REDACTED + "@", redacted)
    for pattern in _KNOWN_TOKEN_PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted


def redact_public_data(value: Any, *, _depth: int = 0) -> Any:
    """Redact a JSON-like value before rendering it in a public report.

    Sensitive mapping fields are replaced wholesale.  Unknown object types
    are represented only by their type name: their ``str``/``repr`` methods
    are never invoked.  A depth limit fails closed on unexpectedly nested
    request-like structures.
    """
    if _depth > 20:
        return REDACTED
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        output = {}
        for key, item in value.items():
            safe_key = (
                redact_text(key) if isinstance(key, str)
                else type(key).__name__
            )
            if isinstance(key, str) and _SENSITIVE_FIELD_RE.search(key):
                output[safe_key] = REDACTED
            else:
                output[safe_key] = redact_public_data(item, _depth=_depth + 1)
        return output
    if isinstance(value, (list, tuple)):
        return [redact_public_data(item, _depth=_depth + 1) for item in value]
    return f"<{type(value).__name__}>"


__all__ = ["REDACTED", "redact_public_data", "redact_text"]
