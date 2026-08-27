"""Confluent / Hermite divided differences.

Layers (do not mix):
- definition: ``repeated_diagonal`` is ``F'(x)``
- recurrence: ``hermite_dd`` (confluent Newton tableau)
- confluence identity: ``confluence.limit_generic_to_degenerate``
- source instantiation: not this package (G/C)

When every node in a window equals ``a`` (``k+1`` copies),
``F[a,...,a] = F^{(k)}(a) / k!``. Distinct endpoints use the Newton
recurrence. Equal endpoints with unequal interior are not rewritten.
"""
from __future__ import annotations

import sympy

from research.representation_invention.dd.newton import newton_first


class HermiteDDError(ValueError):
    """Typed failure for an ill-posed confluent tableau (do not guess)."""


def repeated_diagonal(F: sympy.Expr, z: sympy.Expr, x: sympy.Expr) -> sympy.Expr:
    """Definition of the first confluent diagonal: ``F'(x)``.

    Equal to ``F[x, x]``, not to a 0/0 substitution into ``newton_first``.
    """
    return F.diff(z).xreplace({z: x})


def hermite_dd(
    F: sympy.Expr,
    z: sympy.Expr,
    nodes: list[tuple[sympy.Expr, int]],
) -> sympy.Expr:
    """Confluent divided difference on multiplicity blocks.

    ``nodes`` is ``[(value, multiplicity), ...]`` with multiplicity ``>= 1``.
    Supports ``F[x,y]``, ``F[x,x]``, ``F[x,x,y]``, ``F[x,y,y]``, ``F[x,x,x]``.

    ``F[x, x] = F'(x)`` and ``F[x, x, x] = F''(x) / 2``.
    """
    if not nodes:
        raise ValueError("hermite_dd requires at least one (value, multiplicity)")
    seq: list[sympy.Expr] = []
    for value, multiplicity in nodes:
        try:
            m = int(multiplicity)
        except (TypeError, ValueError) as exc:
            raise ValueError("multiplicity must be an integer >= 1") from exc
        if m < 1 or m != multiplicity:
            raise ValueError("multiplicity must be an integer >= 1")
        seq.extend([value] * m)

    cache: dict[tuple[int, int], sympy.Expr] = {}

    def dd(i: int, j: int) -> sympy.Expr:
        key = (i, j)
        if key in cache:
            return cache[key]
        if i == j:
            val: sympy.Expr = F.xreplace({z: seq[i]})
        elif all(seq[k] == seq[i] for k in range(i, j + 1)):
            order = j - i
            val = F.diff(z, order).xreplace({z: seq[i]}) / sympy.factorial(order)
        elif seq[i] == seq[j]:
            raise HermiteDDError(
                "equal endpoints with unequal interior; use a confluence "
                "limit, not 0/0 substitution"
            )
        elif j == i + 1:
            val = newton_first(F, z, seq[i], seq[j])
        else:
            val = (dd(i + 1, j) - dd(i, j - 1)) / (seq[j] - seq[i])
        cache[key] = val
        return val

    return dd(0, len(seq) - 1)
