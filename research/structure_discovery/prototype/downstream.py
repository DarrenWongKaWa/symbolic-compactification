"""Deterministic downstream-utility probes.

These are NOT human physicist judgments. They ask whether a certified
structured form makes a simple symbolic question easier or more explicit.
Do not treat them as expert preference.
"""
from __future__ import annotations

from typing import Any

from symbolic_compactification import ZERO, parse_expression, verify_equivalent
from symbolic_compactification.models import AdapterError


def index_swap_invariance(text: str, symbols: list, functions: list,
                          pair: tuple[str, str]) -> str | None:
    """Return 'invariant', 'changes', or None if UNKNOWN."""
    try:
        expr = parse_expression(text, symbols, functions=functions or None)
    except AdapterError:
        return None
    a, b = pair
    swapped = str(expr.xreplace(
        {__import__("sympy").Symbol(a): __import__("sympy").Symbol(b),
         __import__("sympy").Symbol(b): __import__("sympy").Symbol(a)}
    ))
    try:
        r = verify_equivalent(text, swapped, symbols, functions=functions or None)
    except AdapterError:
        return None
    if r.verdict == ZERO:
        return "invariant"
    if r.verdict == "NONZERO":
        return "changes"
    return None


def independent_object_count(run: dict) -> int:
    defs = run.get("certified_definitions") or {}
    return len(defs)


def symmetry_exposed(run: dict) -> bool:
    types = set(run.get("hypothesis_types") or [])
    cert = set(run.get("d_certified") or [])
    return ("permutation_orbit" in types or "symmetry_invariant" in types) and bool(
        run.get("n_zero")
    ) and ("D5" in cert or "D2" in cert or "D3" in cert or run.get("n_zero", 0) > 0)


def score_downstream(item: dict, run: dict) -> dict[str, Any]:
    ds = item.get("downstream") or {}
    out = {
        "id": item.get("id"),
        "has_downstream_spec": bool(ds),
        "n_named_aux": independent_object_count(run),
        "symmetry_exposed": symmetry_exposed(run),
        "kernel_exposed": "repeated_kernel" in (run.get("hypothesis_types") or [])
        and (run.get("n_zero") or 0) > 0,
    }
    if ds.get("task") == "index_swap":
        pair = tuple(ds.get("pair") or [])
        if len(pair) == 2:
            ans = index_swap_invariance(
                item["current"], item["symbols"], item.get("functions") or [],
                pair,  # type: ignore[arg-type]
            )
            gold = ds.get("gold_answer")
            out["swap_answer_raw"] = ans
            out["swap_gold"] = gold
            out["swap_match"] = ans == gold if ans and gold else False
    return out
