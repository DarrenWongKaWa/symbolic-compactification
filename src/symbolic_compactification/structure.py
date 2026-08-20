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

from .budgets import run_symbolic_operation
from .models import AdapterError

__all__ = ["expand_finite", "structure_summary", "ordered_atoms",
           "canonical_structure_items"]


# --------------------------------------------------------------------------- #
# deterministic structural ordering (PYTHONHASHSEED-independent)
# --------------------------------------------------------------------------- #

def ordered_atoms(expr: sympy.Expr, kind=None) -> list:
    """Return ``expr``'s atoms in a DETERMINISTIC canonical order.

    ``Expr.atoms`` returns a ``set``; set iteration order depends on
    ``PYTHONHASHSEED`` and is therefore NOT reproducible across processes.
    Any construction, pairing, hash, structural comparison or audit output
    that iterates atoms must go through this helper instead, which sorts by
    canonical ``srepr`` (an explicit sort, independent of hash seeding).

    Args:
        expr: a SymPy expression.
        kind: optional SymPy type (or tuple of types) to filter atoms
              (e.g. ``sympy.Sum``); ``None`` returns every atom.

    Returns:
        A list of atoms sorted by their canonical ``srepr`` string.
    """
    items = expr.atoms() if kind is None else expr.atoms(kind)
    return sorted(items, key=lambda e: sympy.srepr(e))


def canonical_structure_items(expr: sympy.Expr) -> dict:
    """Deterministic, JSON-serializable ordered structural inventory.

    A canonical ordered extraction of the expression's structural content,
    suitable for hashing / structural comparison / audit output: each atom
    category is sorted by canonical ``srepr`` (PYTHONHASHSEED-independent),
    and symbol/function name lists are sorted by name.

    Returns a dict with keys ``sums``, ``products``, ``piecewise`` (each a
    list of canonical ``srepr`` strings), ``free_symbols`` (sorted names) and
    ``indexed_names`` (sorted distinct undefined-function names).
    """
    indexed_names: set[str] = set()
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, sympy.core.function.AppliedUndef):
            indexed_names.add(type(sub).__name__)
    return {
        "sums": [sympy.srepr(s) for s in ordered_atoms(expr, sympy.Sum)],
        "products": [sympy.srepr(p)
                     for p in ordered_atoms(expr, sympy.Product)],
        "piecewise": [sympy.srepr(p)
                      for p in ordered_atoms(expr, sympy.Piecewise)],
        "free_symbols": sorted(s.name for s in expr.free_symbols),
        "indexed_names": sorted(indexed_names),
    }


# --------------------------------------------------------------------------- #
# diagnostic finite-N replay (NEVER a proof for symbolic bounds)
# --------------------------------------------------------------------------- #

def _lower_finite(expr: sympy.Expr) -> sympy.Expr:
    return sympy.expand(expr.doit())


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
    # Evaluate and expand only inside the central finite-diagnostic budget.
    return run_symbolic_operation(
        "finite_expand", _lower_finite, (out,),
        budget_key="finite_expand_seconds")


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
    sums = ordered_atoms(expr, sympy.Sum)
    products = ordered_atoms(expr, sympy.Product)
    piecewise = ordered_atoms(expr, sympy.Piecewise)
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
