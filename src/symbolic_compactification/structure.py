"""Symbolic structure preservation and structure-first diagnostics.

The engine is STRUCTURE-FIRST: the structural representation (``Sum`` with
symbolic bounds, ``Piecewise`` with symbolic conditions, indexed function
applications) is the PRIMARY form. Lowering / finite expansion is a strictly
opt-in diagnostic and NEVER a substitute for symbolic proof.

Two helpers live here:

* ``expand_finite(expr, bounds)`` — "diagnostic / finite-N replay". It
  substitutes concrete integer bounds into a symbolic structure and expands.
  It is explicitly labeled because a finite-N check is NOT a proof for
  symbolic bounds: two expressions can agree at every sampled N yet differ
  symbolically. Use it only to gain intuition or to sanity-check a candidate
  before paying for symbolic adjudication.

* ``structure_summary(expr)`` — a cheap, JSON-serializable description of the
  structural content (how many sums, piecewise branches, indexed calls, free
  symbols and total ops). This lets a caller inspect the highest-level
  representation before deciding whether to lower or expand it.
"""
from __future__ import annotations

from typing import Mapping

import sympy

from .models import AdapterError

__all__ = ["expand_finite", "structure_summary"]


# --------------------------------------------------------------------------- #
# diagnostic finite-N replay (NEVER a proof for symbolic bounds)
# --------------------------------------------------------------------------- #

def expand_finite(expr: sympy.Expr,
                  bounds: Mapping[str, int]) -> sympy.Expr:
    """DIAGNOSTIC / finite-N replay — substitute concrete bounds and expand.

    Replaces the named bound symbols with concrete integers and evaluates any
    ``Sum``/``Product`` whose bounds become numeric, then expands the result.

    WARNING: this is a finite check only. It is NEVER proof for symbolic
    bounds — agreement at finitely many N does not establish a symbolic
    identity. The structural (symbolic) representation remains primary; this
    helper only produces a lowered view for inspection.

    Args:
        expr:   a SymPy expression (typically from the Wolfram adapter).
        bounds: mapping of bound-symbol name -> concrete integer value.

    Returns:
        The lowered, expanded expression.
    """
    if not isinstance(bounds, Mapping):
        raise AdapterError("BOUNDS_MALFORMED")
    out = expr
    # Substitute each named bound symbol with its concrete integer value.
    for name, value in bounds.items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise AdapterError("BOUNDS_MALFORMED")
        # Match symbols by name across the expression's atoms (real/complex
        # assumptions do not matter for a numeric substitution).
        targets = {s for s in out.free_symbols if s.name == name}
        for sym in targets:
            out = out.subs(sym, sympy.Integer(value))
    # Evaluate any remaining concrete Sum/Product nodes.
    out = out.doit()
    return sympy.expand(out)


# --------------------------------------------------------------------------- #
# cheap structural inspection summary
# --------------------------------------------------------------------------- #

def structure_summary(expr: sympy.Expr) -> dict:
    """Cheap, JSON-serializable structural inspection of an expression.

    Reports the highest-level structural content so a caller can decide
    (structure-first) whether to keep, lower or expand a representation:

    * ``sums``             number of ``Sum`` nodes
    * ``products``         number of ``Product`` nodes
    * ``piecewise``        number of ``Piecewise`` nodes
    * ``piecewise_branches`` total branches across all ``Piecewise`` nodes
    * ``indexed_calls``    number of applied undefined functions ``f(...)``
    * ``indexed_names``    sorted distinct undefined-function names
    * ``free_symbols``     sorted free-symbol names
    * ``count_ops``        ``sympy.count_ops`` of the expression
    """
    sums = list(expr.atoms(sympy.Sum))
    products = list(expr.atoms(sympy.Product))
    piecewise = list(expr.atoms(sympy.Piecewise))
    branches = sum(len(p.args) for p in piecewise)

    indexed_names: set[str] = set()
    indexed_calls = 0
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, sympy.core.function.AppliedUndef):
            indexed_calls += 1
            indexed_names.add(type(sub).__name__)

    return {
        "sums": len(sums),
        "products": len(products),
        "piecewise": len(piecewise),
        "piecewise_branches": branches,
        "indexed_calls": indexed_calls,
        "indexed_names": sorted(indexed_names),
        "free_symbols": sorted(s.name for s in expr.free_symbols),
        "count_ops": int(sympy.count_ops(expr, visual=False)),
    }
