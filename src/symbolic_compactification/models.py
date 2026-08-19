"""Shared data types, verdict constants and normalization helpers.

This module contains NO scientific content: only generic math/engineering
plumbing shared by the parser, the verifier and (later) the session layer.
Every record type is JSON-serializable through its ``to_dict()`` method.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import sympy

# --------------------------------------------------------------------------- #
# verdict constants
# --------------------------------------------------------------------------- #

ZERO = "ZERO"          # exact symbolic identity
NONZERO = "NONZERO"    # refuted by an exact counterexample
UNKNOWN = "UNKNOWN"    # fail-closed: simplification undecided, no counterexample

VERIFIER_NAME = "python_sympy_exact_v1"

MAX_SYMBOLS = 40

# Names that may never be used as declared symbol names: they collide with the
# parser's allowed functions/constants whitelist.
RESERVED_NAMES = frozenset({
    "pi", "E", "I", "oo",
    "sin", "cos", "tan", "exp", "log", "sqrt", "Abs", "conjugate", "re", "im",
    "sinh", "cosh", "tanh", "asin", "acos", "atan", "atan2", "Rational",
    # must mirror the parser's allowed-functions policy: admitting a function
    # (e.g. the polygamma family, v0.2) reserves its name as a symbol too
    "polygamma",
    # structural builtins (v0.2) are callables only; never declared symbols
    "Sum", "Product", "Piecewise",
    "Eq", "Ne", "Lt", "Le", "Gt", "Ge", "And", "Or", "Not", "True", "False",
})

# Symbol namespace policy (v0.2): explicit declaration beats built-in, but
# only along the function-builtin axis and only when EXPLICITLY opted in.
#
# * HARD-RESERVED names (constants, Rational, structural builtins) can NEVER
#   be declared, in any namespace: they carry fixed SymPy semantics and an
#   explicit declaration could not safely shadow them.
# * FUNCTION builtins (sin, cos, ..., polygamma) are reserved for the DEFAULT
#   symbol declaration path (``SYMBOL_NAME_RESERVED``). With the explicit
#   opt-in ``normalize_symbols(..., allow_reserved=True)`` a declared symbol
#   named like a function builtin is treated as a SYMBOL — the reserved-name
#   rejection applies only to UNDECLARED collisions.
HARD_RESERVED_NAMES = frozenset({
    "pi", "E", "I", "oo", "Rational",
    "Sum", "Product", "Piecewise",
    "Eq", "Ne", "Lt", "Le", "Gt", "Ge", "And", "Or", "Not", "True", "False",
})
FUNCTION_RESERVED_NAMES = RESERVED_NAMES - HARD_RESERVED_NAMES


def _now_iso() -> str:
    """UTC timestamp string used across session records."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --------------------------------------------------------------------------- #
# error type
# --------------------------------------------------------------------------- #

class AdapterError(Exception):
    """Engine error carrying a stable machine-readable ``.code`` string."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


# --------------------------------------------------------------------------- #
# hashing helper
# --------------------------------------------------------------------------- #

def sha256_text(s: str) -> str:
    """SHA-256 hex digest of a string (utf-8 encoded)."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# symbol normalization
# --------------------------------------------------------------------------- #

def normalize_symbols(symbols: Any, *, allow_reserved: bool = False) -> list[dict]:
    """Normalize a symbol declaration list to canonical dict form.

    Accepts ``["x", "y"]`` or ``[{"name": "x", "real": true, "nonzero": false}, ...]``.
    The string shorthand defaults to ``real=True, nonzero=False``.

    Namespace policy: by default ANY collision with a reserved builtin name
    is rejected (``SYMBOL_NAME_RESERVED``). With the EXPLICIT opt-in
    ``allow_reserved=True`` the precedence "explicit declaration beats
    built-in" applies along the function axis: a declared symbol named like
    a function builtin (sin, cos, ...) is treated as a SYMBOL, while
    hard-reserved names (constants, Rational, structural builtins) are
    ALWAYS rejected. The reserved-name rejection thus applies only to
    undeclared collisions once declarations are explicit.

    Raises:
      AdapterError("CLAIM_SYMBOLS_MALFORMED")  - bad shape, empty list, or duplicates
      AdapterError("SYMBOL_NAME_RESERVED")     - name collides with allowed
                                                 functions/constants
      AdapterError("CLAIM_SYMBOLS_TOO_MANY")   - more than MAX_SYMBOLS symbols
    """
    if not isinstance(symbols, (list, tuple)):
        raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    out: list[dict] = []
    for entry in symbols:
        if isinstance(entry, str):
            name = entry
            out.append({"name": name, "real": True, "nonzero": False})
        elif isinstance(entry, dict) and isinstance(entry.get("name"), str):
            out.append({
                "name": entry["name"],
                "real": bool(entry.get("real", True)),
                "nonzero": bool(entry.get("nonzero", False)),
            })
        else:
            raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    names = [s["name"] for s in out]
    if not names:
        raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    if len(names) != len(set(names)):
        raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    if any(not n or not n.strip() for n in names):
        raise AdapterError("CLAIM_SYMBOLS_MALFORMED")
    forbidden = HARD_RESERVED_NAMES if allow_reserved else RESERVED_NAMES
    if forbidden & set(names):
        raise AdapterError("SYMBOL_NAME_RESERVED")
    if len(names) > MAX_SYMBOLS:
        raise AdapterError("CLAIM_SYMBOLS_TOO_MANY")
    return out


# --------------------------------------------------------------------------- #
# data records (all JSON-serializable via to_dict)
# --------------------------------------------------------------------------- #

@dataclass
class ExpressionRecord:
    """One ingested expression: original text, content hash, parse result."""

    text: str
    sha256: str
    source_path: Optional[str] = None
    parsed_expr: Optional[sympy.Expr] = None
    symbols: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "sha256": self.sha256,
            "source_path": self.source_path,
            # sympy expressions are not JSON-native; store the canonical string
            "parsed_expr": None if self.parsed_expr is None else str(self.parsed_expr),
            "symbols": [dict(s) for s in self.symbols],
        }


@dataclass
class VerificationResult:
    """Outcome of one residual verification. Fail-closed verdict semantics."""

    verdict: str                      # ZERO | NONZERO | UNKNOWN
    residual: str                     # str(expand(current - candidate))
    simplified_residual: str          # str of the adjudicated simplified form
    evidence: list[dict] = field(default_factory=list)
    counterexample: Optional[dict] = None
    probes_tried: int = 0
    seconds: float = 0.0
    verifier: str = VERIFIER_NAME

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "residual": self.residual,
            "simplified_residual": self.simplified_residual,
            "evidence": list(self.evidence),
            "counterexample": self.counterexample,
            "probes_tried": self.probes_tried,
            "seconds": self.seconds,
            "verifier": self.verifier,
        }


@dataclass
class StepRecord:
    """One compactification step: candidate vs. current, residual + verdict."""

    step: int
    current_hash: str
    candidate_hash: str
    candidate_text: str
    residual: Optional[str]
    verdict: str
    evidence: list[dict] = field(default_factory=list)
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "current_hash": self.current_hash,
            "candidate_hash": self.candidate_hash,
            "candidate_text": self.candidate_text,
            "residual": self.residual,
            "verdict": self.verdict,
            "evidence": list(self.evidence),
            "timestamp": self.timestamp,
        }


@dataclass
class SessionState:
    """Minimal session container; a later task owns JSON (de)serialization."""

    run_id: str
    created_at: str = field(default_factory=_now_iso)
    current: Optional[ExpressionRecord] = None
    steps: list[StepRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "current": None if self.current is None else self.current.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
        }
