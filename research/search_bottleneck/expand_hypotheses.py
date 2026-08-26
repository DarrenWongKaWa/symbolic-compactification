"""Expand hypothesis_definitions into candidate_text, then verify.

Experimental helper. Not a production promotion path.
"""
from __future__ import annotations

from typing import Optional

from symbolic_compactification import UNKNOWN, verify_equivalent
from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import parse_expression


def expand_candidate(candidate_text: str, definitions: dict, symbols: list,
                     functions: list) -> tuple[str, Optional[str]]:
    """Return (expanded_text, error). Definitions are substituted by name."""
    if not definitions:
        return candidate_text, None
    extra = list(functions or [])
    extra.extend(definitions.keys())
    try:
        expr = parse_expression(
            candidate_text, symbols, functions=sorted(set(extra)))
    except AdapterError as exc:
        return candidate_text, exc.code
    try:
        for name, body in definitions.items():
            body_expr = parse_expression(
                body, symbols, functions=sorted(set(extra)))
            # Replace undefined-function applications Name(...) and Symbol Name
            targets = [
                n for n in expr.atoms()
                if getattr(n, "name", None) == name
            ]
            for t in targets:
                expr = expr.subs(t, body_expr)
            for sub in list(expr.atoms()):
                if type(sub).__name__ == name or (
                    hasattr(sub, "func") and getattr(sub.func, "__name__", "") == name
                ):
                    try:
                        expr = expr.replace(sub.func, lambda *a: body_expr)
                    except Exception:
                        pass
        return str(expr), None
    except AdapterError as exc:
        return candidate_text, exc.code
    except Exception as exc:
        return candidate_text, type(exc).__name__


def verify_with_definitions(current: str, candidate_text: str, definitions: dict,
                            symbols: list, functions: list):
    expanded, err = expand_candidate(
        candidate_text, definitions or {}, symbols, functions or [])
    if err:
        class _R:
            verdict = UNKNOWN
            seconds = 0.0
            evidence = [{"kind": "definition_expand_failed", "code": err}]
            counterexample = None
        return expanded, _R
    extra = list(functions or [])
    extra.extend((definitions or {}).keys())
    result = verify_equivalent(
        current, expanded, symbols, functions=extra or None)
    return expanded, result
