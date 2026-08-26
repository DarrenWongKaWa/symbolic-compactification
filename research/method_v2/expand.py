"""Mandatory closed-candidate expansion (Method v2).

Engine semantics unchanged. Unexpanded names must not reach verify as if
they were the original namespace.
"""
from __future__ import annotations

import re
from typing import Optional

from symbolic_compactification import UNKNOWN, verify_equivalent
from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import parse_expression


def _clean_body(name: str, body: str) -> str:
    body = (body or "").strip()
    patterns = [
        rf"^{re.escape(name)}\s*\([^)]*\)\s*:?=\s*",
        rf"^{re.escape(name)}\s*:?=\s*",
        rf"^{re.escape(name)}\s*=\s*",
    ]
    for pat in patterns:
        body = re.sub(pat, "", body, count=1)
    return body.strip()


def expand_text(candidate_text: str, definitions: dict | None) -> str:
    text = candidate_text
    if not definitions:
        return text
    items = sorted(definitions.items(), key=lambda kv: -len(kv[0]))
    for name, body in items:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            continue
        repl = f"({_clean_body(name, body)})"
        text = re.sub(rf"\b{re.escape(name)}\s*\([^)]*\)", repl, text)
        text = re.sub(rf"\b{re.escape(name)}\b", repl, text)
    return text


def expand_and_verify(current: str, candidate_text: str, definitions: dict,
                      symbols: list, functions: list | None):
    expanded = expand_text(candidate_text, definitions or {})
    try:
        parse_expression(expanded, symbols, functions=functions or None)
    except AdapterError as exc:
        class _R:
            verdict = UNKNOWN
            seconds = 0.0
            evidence = [{"kind": "definition_expand_failed", "code": exc.code}]
            counterexample = None
        return expanded, _R()
    result = verify_equivalent(
        current, expanded, symbols, functions=functions or None)
    return expanded, result
