"""Newton divided differences.

Layers (do not mix):
- definition: ``newton_first``
- recurrence: ``newton_table``
- confluence identity: ``confluence.limit_generic_to_degenerate``
- source instantiation: not this package (G/C)

Generic mathematics only. Coincident nodes are left as 0/0; they are
not rewritten to a derivative.
"""
from __future__ import annotations

import sympy


def newton_first(
    F: sympy.Expr,
    z: sympy.Expr,
    x: sympy.Expr,
    y: sympy.Expr,
) -> sympy.Expr:
    """Definition of the first Newton divided difference ``F[x, y]``.

    ``F[x, y] = (F(x) - F(y)) / (x - y)``

    This is not a recurrence and not a limit. Substituting ``y = x``
    yields 0/0, not ``F'(x)``.
    """
    return (F.xreplace({z: x}) - F.xreplace({z: y})) / (x - y)


def newton_table(
    F: sympy.Expr,
    z: sympy.Expr,
    nodes: list[sympy.Expr],
) -> sympy.Expr:
    """Newton tableau recurrence ``F[x0, ..., xk]``.

    Base: ``F[xi] = F(xi)``.
    Two-node step uses the ``newton_first`` definition.
    Higher order: ``(F[x1..xk] - F[x0..x_{k-1}]) / (xk - x0)``.

    Does not take confluence limits when nodes coincide.
    """
    if not nodes:
        raise ValueError("newton_table requires at least one node")
    seq = list(nodes)
    cache: dict[tuple[int, int], sympy.Expr] = {}

    def dd(i: int, j: int) -> sympy.Expr:
        key = (i, j)
        if key in cache:
            return cache[key]
        if i == j:
            val: sympy.Expr = F.xreplace({z: seq[i]})
        elif j == i + 1:
            val = newton_first(F, z, seq[i], seq[j])
        else:
            val = (dd(i + 1, j) - dd(i, j - 1)) / (seq[j] - seq[i])
        cache[key] = val
        return val

    return dd(0, len(seq) - 1)
