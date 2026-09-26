"""Shared helpers for the many-body verifiers.

Statuses reuse the derivation-audit vocabulary. ``CERTIFIED_BY_RULE`` means
a local exact engine result plus a named theorem whose hypotheses were
checked mechanically or declared; it is never an engine ZERO for the global
object (an infinite sum, an integral, a remainder class).
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Mapping, Optional

import sympy

from ..audit.schema import (ASSUMPTION_REQUIRED, CERTIFIED_BY_RULE, NONZERO,
                            UNKNOWN)
from ..models import AdapterError, normalize_symbols
from ..parser import parse_expression

__all__ = [
    "ASSUMPTION_REQUIRED", "CERTIFIED_BY_RULE", "NONZERO", "UNKNOWN",
    "DISTRIBUTION_FUNCTIONS", "ManyBodyResult", "Namespace", "certificate_hash",
    "sample_points",
]

# Reserved undefined-function names a claim may use for the distributions.
DISTRIBUTION_FUNCTIONS = ("nF", "nB")

NUMERIC_AGREES = "AGREES"
NUMERIC_DISAGREES = "DISAGREES"
NUMERIC_UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ManyBodyResult:
    """Outcome of one many-body equivalence check."""

    kind: str
    status: str
    rule_id: str
    reasons: tuple[str, ...]
    derived: str
    symbolic_verdict: str
    numeric: Mapping[str, Any] = field(default_factory=dict)
    certificate: Mapping[str, Any] = field(default_factory=dict)
    certificate_hash: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "status": self.status,
            "rule_id": self.rule_id,
            "reasons": list(self.reasons),
            "derived": self.derived,
            "symbolic_verdict": self.symbolic_verdict,
            "numeric": dict(self.numeric),
            "certificate": dict(self.certificate),
            "certificate_hash": self.certificate_hash,
        }


class Namespace:
    """Declared symbols plus the many-body names, parsed consistently."""

    def __init__(self, symbols: Any, functions: Any = None, *,
                 complex_names: tuple[str, ...] = ()):
        declared = [s for s in normalize_symbols(symbols)
                    if s["name"] not in complex_names]
        declared += [{"name": name, "real": False, "nonzero": False}
                     for name in complex_names]
        self.declared = declared
        user_functions = [str(name) for name in (functions or [])]
        self.functions = sorted(set(user_functions) | set(DISTRIBUTION_FUNCTIONS))

    def parse(self, text: str) -> sympy.Expr:
        return parse_expression(text, self.declared, functions=self.functions)

    def symbol(self, name: str) -> sympy.Symbol:
        if name not in {s["name"] for s in self.declared}:
            raise AdapterError("UNDECLARED_OR_DISALLOWED_NAME")
        value = self.parse(name)
        if not isinstance(value, sympy.Symbol):
            raise AdapterError("UNDECLARED_OR_DISALLOWED_NAME")
        return value

    def declared_for(self, *exprs: sympy.Expr) -> list[dict]:
        """Declarations restricted to symbols the expressions use.

        Unused symbols would only inflate the verifier's probe lattice.
        """
        used = set().union(*(e.free_symbols for e in exprs)) if exprs else set()
        names = {sym.name for sym in used}
        return [s for s in self.declared if s["name"] in names] or self.declared[:1]

    def positives(self, names: tuple[str, ...]) -> tuple[sympy.Symbol, ...]:
        return tuple(self.symbol(name) for name in names)

    def real(self, name: str) -> bool:
        return any(s["name"] == name and s["real"] for s in self.declared)


def fermi(beta: sympy.Expr, x: sympy.Expr) -> sympy.Expr:
    return 1 / (sympy.exp(beta * x) + 1)


def bose(beta: sympy.Expr, x: sympy.Expr) -> sympy.Expr:
    return 1 / (sympy.exp(beta * x) - 1)


def expand_distributions(expr: sympy.Expr, beta: sympy.Expr) -> sympy.Expr:
    """Replace nF(x), nB(x) by their explicit exponential forms."""
    expr = expr.replace(sympy.Function("nF"), lambda x: fermi(beta, x))
    return expr.replace(sympy.Function("nB"), lambda x: bose(beta, x))


def canonical_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def certificate_hash(data: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sample_points(free: set, *, positive: tuple[sympy.Symbol, ...] = (),
                  count: int = 3, seed: int = 20260926) -> list[dict]:
    """Deterministic rational sample points away from zero.

    Real symbols get values in [-2, 2]; declared-positive ones in [1, 4];
    complex symbols get a nonzero real and imaginary part.
    """
    rng = random.Random(seed)
    ordered = sorted(free, key=lambda s: s.name)

    def rational(lo: float, hi: float) -> sympy.Rational:
        value = Fraction(rng.uniform(lo, hi)).limit_denominator(97)
        if value == 0:
            value = Fraction(3, 7)
        return sympy.Rational(value.numerator, value.denominator)

    points = []
    for _ in range(count):
        point = {}
        for sym in ordered:
            if sym in positive:
                point[sym] = rational(1.0, 4.0)
            elif sym.is_real:
                sign = rng.choice((-1, 1))
                point[sym] = sign * rational(0.2, 2.0)
            else:
                point[sym] = rational(0.2, 2.0) + sympy.I * rational(0.2, 2.0)
        points.append(point)
    return points
