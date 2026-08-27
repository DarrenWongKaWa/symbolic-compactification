"""Confluence identity: generic node → degenerate node.

Layers (do not mix):
- definition / recurrence: ``newton``, ``hermite``
- confluence identity: ``limit_generic_to_degenerate``
- source instantiation: not this package (G/C)

Uses ``sympy.limit`` only. Failures raise ``ConfluenceLimitError``;
they are not repaired by substitution, series, or 0/0 cancellation.
"""
from __future__ import annotations

import sympy


class ConfluenceLimitError(ValueError):
    """Typed failure when ``sympy.limit`` does not evaluate a confluence."""


def limit_generic_to_degenerate(
    generic: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
) -> sympy.Expr:
    """Confluence identity ``lim_{var → point} generic``.

    Not a divided-difference definition and not source instantiation.
    """
    try:
        result = sympy.limit(generic, var, point)
    except Exception as exc:
        raise ConfluenceLimitError(
            f"sympy.limit failed: {type(exc).__name__}: {exc}"
        ) from exc
    if isinstance(result, sympy.Limit):
        raise ConfluenceLimitError(f"sympy.limit did not evaluate: {result}")
    if isinstance(result, sympy.Expr) and result.has(sympy.Limit):
        raise ConfluenceLimitError(
            f"sympy.limit returned an unevaluated Limit: {result}"
        )
    return result
