"""General numeric support for a scalar claim ``lhs == rhs``.

Many derivation steps are integrals, limits or asymptotic approximations that
SymPy cannot close symbolically, so the exact engine returns ``UNKNOWN`` and the
step is handed to a human. For those steps a high-precision numeric comparison is
honest evidence: it can *refute* a wrong rewrite with an explicit counterexample,
and it can *support* a correct one, but it never proves the identity. The result
is therefore ``NUMERICAL_SUPPORT`` -- the same status the real-frequency integral
check uses -- never ``CERTIFIED_BY_RULE`` and never an engine ``ZERO``.

Two habits make the support trustworthy rather than a single lucky probe, and
both are the point of this module over a bare three-point check:

* **Many witnesses, including adversarial edges.** The claim is evaluated at a
  batch of deterministic generic sample points *and* at coincidence points where
  two declared real symbols are driven close together. Divided-difference and
  removable-limit sign errors (the ``n = m`` branch of a Matsubara pair, for
  instance) hide exactly in the region generic sampling under-covers.
* **A non-vacuous guard.** If both sides stay within ``VACUOUS_FLOOR`` of zero at
  every witness the check returns ``UNAVAILABLE`` instead of ``AGREES`` -- a
  ``0 == 0`` coincidence is not evidence for an identity.

Disagreement is reported with the offending point and both values so the finding
is reproducible, mirroring the exact engine's ``NONZERO`` counterexample.
"""
from __future__ import annotations

import cmath
from typing import Any, Optional

import sympy

from ..models import AdapterError
from ._common import (NUMERIC_AGREES, NUMERIC_DISAGREES, NUMERIC_UNAVAILABLE,
                      Namespace, certificate_hash, expand_distributions,
                      sample_points, text_hash)
from .integrals import NUMERICAL_SUPPORT

# Precision of each evaluation and the default count of generic witnesses.
EVAL_DPS = 50
DEFAULT_COUNT = 12
# A witness is only informative if at least one side clears this in magnitude.
VACUOUS_FLOOR = 1e-6
# How close a coincidence edge drives two symbols, and the pair budget.
COINCIDENCE_EPS = sympy.Rational(1, 1000)
MAX_EDGE_PAIRS = 6


def _evaluate(expr: sympy.Expr, point: dict, dps: int) -> Optional[complex]:
    """Numeric value of ``expr`` at ``point``; ``None`` when it is unusable."""
    try:
        value = complex(sympy.N(expr.subs(point), dps))
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return None
    if cmath.isinf(value) or cmath.isnan(value):
        return None
    return value


def _rel_diff(lhs: complex, rhs: complex) -> float:
    return abs(lhs - rhs) / max(1.0, abs(rhs))


def _edge_points(free: set, positive: tuple, base_seed: int) -> list[dict]:
    """Coincidence witnesses: two declared real symbols driven close together."""
    real = sorted((s for s in free if s.is_real), key=lambda s: s.name)
    edges: list[dict] = []
    seed = base_seed
    for i in range(len(real)):
        for j in range(i + 1, len(real)):
            if len(edges) >= MAX_EDGE_PAIRS:
                return edges
            seed += 1
            base = sample_points(free, positive=positive, count=1, seed=seed)[0]
            point = dict(base)
            point[real[j]] = point[real[i]] + COINCIDENCE_EPS
            edges.append(point)
    return edges


def check_numeric_equivalence(lhs: str, rhs: str, *, symbols: Any,
                              functions: Any = None, beta: str | None = None,
                              positive: tuple[str, ...] = (),
                              count: int = DEFAULT_COUNT,
                              tolerance: str = "1e-9") -> dict:
    """Compare ``lhs`` and ``rhs`` numerically over the declared symbols.

    Returns a ``NUMERICAL_SUPPORT`` record with ``numeric`` one of ``AGREES`` /
    ``DISAGREES`` / ``UNAVAILABLE``. ``DISAGREES`` carries a ``counterexample``.
    """
    try:
        space = Namespace(symbols, functions)
        b = space.symbol(beta) if beta else None
        left = space.parse(lhs)
        right = space.parse(rhs)
        pos = space.positives(tuple(positive))
        if b is not None:
            left, right = expand_distributions(left, b), expand_distributions(right, b)
    except AdapterError as exc:
        return {"status": NUMERICAL_SUPPORT, "numeric": NUMERIC_UNAVAILABLE,
                "reasons": [f"PARSE_FAILED:{exc.code}"]}

    free = left.free_symbols | right.free_symbols
    positive_syms = ((b,) if b is not None else ()) + pos
    tol = float(tolerance)

    edges = _edge_points(free, positive_syms, base_seed=20260926 + count)
    witnesses = sample_points(free, positive=positive_syms, count=count) + edges

    tried = 0
    magnitude = 0.0
    worst_rel = 0.0
    worst_point: Optional[dict] = None
    worst_values: tuple = ()
    for point in witnesses:
        left_val = _evaluate(left, point, EVAL_DPS)
        right_val = _evaluate(right, point, EVAL_DPS)
        if left_val is None and right_val is None:
            continue
        if left_val is None or right_val is None:
            # One side blows up while the other stays finite: a disagreement.
            worst_rel, worst_point = float("inf"), point
            worst_values = (left_val, right_val)
            tried += 1
            break
        tried += 1
        magnitude = max(magnitude, abs(left_val), abs(right_val))
        rel = _rel_diff(left_val, right_val)
        if rel > worst_rel:
            worst_rel, worst_point, worst_values = rel, point, (left_val, right_val)

    if tried == 0:
        return {"status": NUMERICAL_SUPPORT, "numeric": NUMERIC_UNAVAILABLE,
                "reasons": ["INSUFFICIENT_WITNESSES"]}
    if worst_rel <= tol and magnitude <= VACUOUS_FLOOR:
        return {"status": NUMERICAL_SUPPORT, "numeric": NUMERIC_UNAVAILABLE,
                "points": tried, "reasons": ["VACUOUS_BOTH_SIDES_NEAR_ZERO"]}

    certificate = {
        "check": "numeric_equivalence",
        "lhs_sha256": text_hash(lhs),
        "rhs_sha256": text_hash(rhs),
        "witnesses": tried,
        "edge_pairs": len(edges),
        "eval_dps": EVAL_DPS,
        "tolerance": tolerance,
    }
    agrees = worst_rel <= tol
    result = {
        "status": NUMERICAL_SUPPORT,
        "numeric": NUMERIC_AGREES if agrees else NUMERIC_DISAGREES,
        "points": tried,
        "max_rel_diff": "inf" if worst_rel == float("inf") else format(worst_rel, ".3g"),
        "reasons": [],
        "certificate": certificate,
        "certificate_hash": certificate_hash(certificate),
    }
    if not agrees and worst_point is not None:
        result["counterexample"] = {
            "point": {s.name: str(v) for s, v in worst_point.items()},
            "lhs_value": None if worst_values[0] is None else str(worst_values[0]),
            "rhs_value": None if worst_values[1] is None else str(worst_values[1]),
        }
    return result
