"""Translation fidelity checking for adapter and representation audits.

A GENERIC helper that judges how faithfully one textual representation of an
expression corresponds to another — e.g. an adapter translation versus the
source. It is structural and semantic, NOT textual: SymPy canonicalization
that harmlessly reorders commutative ``Add``/``Mul`` operands must never be
counted against fidelity.

Fidelity classes (returned in ``result["fidelity"]``, ordered from strongest
to weakest):

* ``BYTE_IDENTICAL``            - the two strings are exactly the same bytes.
* ``STRUCTURALLY_IDENTICAL``    - distinct text, identical canonical AST
                                  (``srepr``), so only presentation differs.
* ``SEMANTICALLY_EQUIVALENT``   - matching structural content (Sum counts and
                                  bounds, Piecewise branches/conditions,
                                  undefined-function calls, free symbols) AND
                                  a zero semantic residual (``simplify(a-b)==0``).
* ``MISMATCH``                  - provably different: a structural feature
                                  differs (e.g. a Sum bound changed) or the
                                  residual is a concrete nonzero constant.
* ``UNKNOWN``                   - cannot be determined (a side fails to parse,
                                  or the residual is inconclusive). Fail-closed:
                                  inconclusive is never reported as equivalent.

The comparison dimensions: Sum counts/bounds, Product counts, Piecewise
branches and conditions, undefined-function calls, free/bound symbols and the
semantic residual. Both sides are parsed under the SAME declared symbol
assumptions, so the assumption axis is consistent by construction; any
assumption-driven difference surfaces through the free-symbol comparison.
No scientific content is assumed — generic structures only.
"""
from __future__ import annotations

from typing import Any, Optional

import sympy

from .models import AdapterError, normalize_symbols
from .parser import parse_expression
from .structure import ordered_atoms

__all__ = [
    "translation_fidelity",
    "FIDELITY_BYTE_IDENTICAL",
    "FIDELITY_STRUCTURALLY_IDENTICAL",
    "FIDELITY_SEMANTICALLY_EQUIVALENT",
    "FIDELITY_MISMATCH",
    "FIDELITY_UNKNOWN",
    "FIDELITY_CLASSES",
]

FIDELITY_BYTE_IDENTICAL = "BYTE_IDENTICAL"
FIDELITY_STRUCTURALLY_IDENTICAL = "STRUCTURALLY_IDENTICAL"
FIDELITY_SEMANTICALLY_EQUIVALENT = "SEMANTICALLY_EQUIVALENT"
FIDELITY_MISMATCH = "MISMATCH"
FIDELITY_UNKNOWN = "UNKNOWN"

FIDELITY_CLASSES = (
    FIDELITY_BYTE_IDENTICAL,
    FIDELITY_STRUCTURALLY_IDENTICAL,
    FIDELITY_SEMANTICALLY_EQUIVALENT,
    FIDELITY_MISMATCH,
    FIDELITY_UNKNOWN,
)


# --------------------------------------------------------------------------- #
# structural feature extraction (deterministic; PYTHONHASHSEED-independent)
# --------------------------------------------------------------------------- #

def _structural_features(expr: sympy.Expr) -> dict:
    """Deterministic ordered structural inventory used for comparison.

    Every collection is sorted (by canonical ``srepr`` / name) so the
    comparison never depends on hash seeding. Captures Sum counts AND bounds,
    Product counts, Piecewise branches and conditions, undefined-function
    calls, and free symbols.
    """
    piecewise = ordered_atoms(expr, sympy.Piecewise)
    branches = []
    for p in piecewise:
        for branch in p.args:  # each branch is (value, condition)
            branches.append(sympy.srepr(branch))

    function_calls = sorted(
        sympy.srepr(sub)
        for sub in sympy.preorder_traversal(expr)
        if isinstance(sub, sympy.core.function.AppliedUndef))

    return {
        "sums": [sympy.srepr(s) for s in ordered_atoms(expr, sympy.Sum)],
        "products": [sympy.srepr(p)
                     for p in ordered_atoms(expr, sympy.Product)],
        "piecewise_branches": sorted(branches),
        "function_calls": function_calls,
        "free_symbols": sorted(s.name for s in expr.free_symbols),
    }


def _normalize_declared(symbols: Any) -> list:
    """Accept a list of names, a list of dicts, or None -> declared list."""
    if symbols is None:
        return []
    items = list(symbols)
    if not items:
        return []
    return normalize_symbols(items)


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #

def translation_fidelity(source_text: str, target_text: str, *,
                         symbols: Any = None,
                         functions: Optional[list] = None) -> dict:
    """Judge the fidelity of ``target_text`` relative to ``source_text``.

    Args:
        source_text: the reference representation.
        target_text: the representation being compared to the reference.
        symbols:     declared symbols (names or dict form) both sides are
                     parsed under; ``None``/empty declares none.
        functions:   declared undefined-function names (indexed calls).

    Returns:
        A dict with:
          * ``fidelity``  - one of ``FIDELITY_CLASSES``;
          * ``reason``    - a short human-readable justification;
          * ``structure`` - the deterministic structural feature inventory of
                            each side (present when both parse), useful for
                            explaining a ``MISMATCH``.

    The judgement is fail-closed: anything that cannot be established as
    identical/equivalent is ``UNKNOWN`` (never claimed equivalent), and a
    provable difference is ``MISMATCH``.
    """
    # Byte identity needs no parsing at all.
    if isinstance(source_text, str) and isinstance(target_text, str) \
            and source_text == target_text:
        return {"fidelity": FIDELITY_BYTE_IDENTICAL,
                "reason": "byte-identical text"}

    declared = _normalize_declared(symbols)
    try:
        source_expr = parse_expression(source_text, declared,
                                       functions=functions)
        target_expr = parse_expression(target_text, declared,
                                       functions=functions)
    except (AdapterError, Exception):
        return {"fidelity": FIDELITY_UNKNOWN,
                "reason": "one or both sides failed to parse under the "
                          "declared namespace"}

    source_rep = sympy.srepr(source_expr)
    target_rep = sympy.srepr(target_expr)
    if source_rep == target_rep:
        return {"fidelity": FIDELITY_STRUCTURALLY_IDENTICAL,
                "reason": "identical canonical AST (presentation-only "
                          "difference)"}

    source_feat = _structural_features(source_expr)
    target_feat = _structural_features(target_expr)
    result_structure = {"source": source_feat, "target": target_feat}

    # A structural feature difference is a provable mismatch (e.g. a Sum
    # bound changed, a Piecewise branch added, a function call altered).
    differing = sorted(k for k in source_feat
                       if source_feat[k] != target_feat[k])
    if differing:
        return {"fidelity": FIDELITY_MISMATCH,
                "reason": "structural features differ: "
                          + ", ".join(differing),
                "structure": result_structure}

    # Structural content matches: use the same bounded exact verifier as every
    # certification path. Fidelity never owns an unbounded simplify bypass.
    from .verifier import verify_equivalent
    verification = verify_equivalent(
        source_text, target_text, declared, functions=functions)
    if verification.verdict == "ZERO":
        return {"fidelity": FIDELITY_SEMANTICALLY_EQUIVALENT,
                "reason": "matching structure and a zero semantic residual",
                "structure": result_structure}
    if verification.verdict == "NONZERO":
        return {"fidelity": FIDELITY_MISMATCH,
                "reason": "nonzero semantic residual proven by an exact "
                          "verifier counterexample",
                "structure": result_structure}
    return {"fidelity": FIDELITY_UNKNOWN,
            "reason": "inconclusive semantic residual (fail-closed)",
            "structure": result_structure}
