"""Exact residual verifier (Python/SymPy only). Fail-closed verdict semantics.

Pipeline for R := current - candidate:
  1. diff = expand(R); the residual string field is str(diff).
  2. simp = simplify(diff); if count_ops(simp) exceeds the ops cap, adjudicate
     the expanded form instead (pathological-growth safety net).
  3. simp == 0                     -> ZERO  (exact_symbolic_zero)
  4. expand_complex + simplify == 0-> ZERO  (complex normalization branch)
  5. exact rational probe lattice  -> NONZERO only when SymPy can PROVE a
     probe value nonzero: ``value != 0 and value.equals(0) is False``.
  6. otherwise                     -> UNKNOWN (fail-closed).

Only an exact symbolic zero yields ZERO; only a proven exact counterexample
yields NONZERO; every undecided or exceptional path yields UNKNOWN.
"""
from __future__ import annotations

import time
from itertools import product
from typing import Any, Optional

import sympy

from .models import (AdapterError, NONZERO, UNKNOWN, VERIFIER_NAME, ZERO,
                     VerificationResult, normalize_symbols)
from .parser import parse_expression

# --------------------------------------------------------------------------- #
# exact probe lattice (Rationals only — no floats, ever)
# --------------------------------------------------------------------------- #

REAL_PROBES = (-2, -1, -sympy.Rational(1, 2), sympy.Rational(1, 2), 1, 2)
COMPLEX_PROBES = (1, -1, sympy.I, -sympy.I, 1 + sympy.I, 1 - sympy.I)
MAX_PROBES = 128

# --------------------------------------------------------------------------- #
# verify policy (limits are POLICY, never silently edited constants)
# --------------------------------------------------------------------------- #
# Every bound that trades cost against adjudication power lives here so it can
# be reviewed, tuned per call, and recorded in evidence — instead of drifting
# as an anonymous literal in the pipeline.

_DEFAULT_VERIFY_POLICY: dict = {
    # pathological-growth safety net: if a simplified residual exceeds this
    # op count, adjudicate the expanded form instead
    "simplify_ops_cap": 8000,
}

# module-level view exposed for inspection/tests; mutate via set_verify_policy()
VERIFY_POLICY: dict = dict(_DEFAULT_VERIFY_POLICY)


def get_verify_policy() -> dict:
    """Return a fresh copy of the current default verify policy."""
    return dict(VERIFY_POLICY)


def set_verify_policy(**overrides) -> dict:
    """Update module-level verify policy defaults. Unknown keys are rejected."""
    unknown = set(overrides) - set(_DEFAULT_VERIFY_POLICY)
    if unknown:
        raise AdapterError("VERIFY_POLICY_KEY_UNKNOWN")
    VERIFY_POLICY.update(overrides)
    return get_verify_policy()


def _effective_verify_policy(policy: Optional[dict]) -> dict:
    merged = get_verify_policy()
    if policy:
        unknown = set(policy) - set(_DEFAULT_VERIFY_POLICY)
        if unknown:
            raise AdapterError("VERIFY_POLICY_KEY_UNKNOWN")
        merged.update(policy)
    return merged


_SKIPPED_PROBE_VALUES = (
    sympy.nan, sympy.oo, -sympy.oo, sympy.zoo,
    sympy.I * sympy.oo, -sympy.I * sympy.oo,
)


def _unknown_result(reason_kind: str, detail: dict,
                    seconds: float, residual: str = "") -> VerificationResult:
    return VerificationResult(
        verdict=UNKNOWN,
        residual=residual,
        simplified_residual="",
        evidence=[{"kind": reason_kind, **detail}],
        counterexample=None,
        probes_tried=0,
        seconds=round(seconds, 4),
        verifier=VERIFIER_NAME,
    )


def _probe_sets_for(symbols: list[dict]) -> list[list]:
    """Per-symbol exact probe sets, chosen by each symbol's declared real flag."""
    return [list(REAL_PROBES) if s["real"] else list(COMPLEX_PROBES)
            for s in symbols]


# --------------------------------------------------------------------------- #
# main API
# --------------------------------------------------------------------------- #

def verify_equivalent(current_expression: Any, candidate_expression: Any,
                      symbols: Any, assumptions: Optional[dict] = None, *,
                      max_probes: int = MAX_PROBES,
                      policy: Optional[dict] = None) -> VerificationResult:
    """Adjudicate whether ``current`` and ``candidate`` are symbolically equal.

    Both sides are raw strings parsed through the strict whitelist parser.
    ``assumptions`` is accepted for interface stability and recorded in the
    evidence metadata; per-symbol assumptions come from the ``symbols``
    declarations. ``policy`` optionally overrides verify-policy limits for
    this single call. Never raises: any failure path returns an UNKNOWN
    VerificationResult (fail-closed).
    """
    t0 = time.time()
    pol = _effective_verify_policy(policy)

    def _seconds() -> float:
        return time.time() - t0

    # -- construction / parse phase (fail closed on AdapterError) ----------- #
    try:
        declared = normalize_symbols(symbols)
        current = parse_expression(current_expression, declared)
        candidate = parse_expression(candidate_expression, declared)
    except AdapterError as exc:
        return _unknown_result(
            "construction_or_parse_failed",
            {"code": exc.code,
             **({"assumptions": assumptions} if assumptions else {})},
            _seconds())
    except Exception:  # defensive: never raise to the caller
        return _unknown_result("construction_or_parse_failed", {"code": "UNEXPECTED"},
                               _seconds())

    # -- verification pipeline (any unexpected exception -> UNKNOWN) -------- #
    try:
        diff = sympy.expand(current - candidate)
        residual_str = str(diff)

        simp = sympy.simplify(diff)
        if sympy.count_ops(simp, visual=False) > pol["simplify_ops_cap"]:
            simp = diff  # pathological growth: adjudicate the expanded form

        result = VerificationResult(
            verdict=UNKNOWN,
            residual=residual_str,
            simplified_residual=str(simp),
            evidence=[],
            counterexample=None,
            probes_tried=0,
            seconds=0.0,
            verifier=VERIFIER_NAME,
        )
        if assumptions:
            result.evidence.append({"kind": "declared_assumptions",
                                    "assumptions": assumptions})

        # 3) exact symbolic zero
        if simp == 0:
            result.verdict = ZERO
            result.evidence.append({"kind": "exact_symbolic_zero",
                                    "simplified_difference": "0"})
            result.seconds = round(_seconds(), 4)
            return result

        # 4) complex normalization branch (re/im/conjugate canonicalization)
        try:
            complex_normalized = sympy.expand_complex(simp)
            if sympy.count_ops(complex_normalized, visual=False) <= pol["simplify_ops_cap"]:
                simp2 = sympy.simplify(complex_normalized)
                if simp2 == 0:
                    result.verdict = ZERO
                    result.simplified_residual = str(simp2)
                    result.evidence.append(
                        {"kind": "exact_symbolic_zero_after_complex_normalization",
                         "normalized_difference": str(complex_normalized),
                         "complex_normalized": True})
                    result.seconds = round(_seconds(), 4)
                    return result
        except Exception:
            pass  # complex normalization is best-effort; fall through to probes

        # 5) NONZERO branch: exact probe counterexamples.
        # substitution keys MUST be the expression's own symbol objects:
        # string keys build assumption-less symbols that never match the
        # parsed Symbol(name, real=...) objects.
        expr_symbols = {str(s): s for s in diff.free_symbols}
        probe_sets = _probe_sets_for(declared)
        counterexample: Optional[dict] = None
        tried = 0
        for combo in product(*probe_sets):
            if tried >= max_probes:
                break
            tried += 1
            point = {expr_symbols[s["name"]]: combo[j]
                     for j, s in enumerate(declared)
                     if s["name"] in expr_symbols}
            try:
                value = sympy.simplify(diff.subs(point))
            except Exception:
                continue  # singular/degenerate probe: never a counterexample
            if value in _SKIPPED_PROBE_VALUES:
                continue
            # a probe counts as a counterexample ONLY when sympy can PROVE the
            # exact value nonzero; values where equals(0) is None (e.g. nested
            # radicals that are 0 but not canonicalized) are skipped.
            if value != 0 and value.equals(0) is False:
                counterexample = {"point": {str(k): str(v) for k, v in point.items()},
                                  "exact_value": str(value)}
                break

        result.probes_tried = tried
        if counterexample is not None:
            result.verdict = NONZERO
            result.counterexample = counterexample
            result.evidence.append({"kind": "exact_counterexample", **counterexample})
        else:
            result.verdict = UNKNOWN
            result.evidence.append(
                {"kind": "simplification_undecided_no_exact_counterexample",
                 "probes_tried": tried})
        result.seconds = round(_seconds(), 4)
        return result

    except Exception:
        # fail closed: any unexpected failure anywhere in the pipeline
        return _unknown_result("simplification_undecided_no_exact_counterexample",
                               {"code": "UNEXPECTED_PIPELINE_ERROR"},
                               _seconds())
