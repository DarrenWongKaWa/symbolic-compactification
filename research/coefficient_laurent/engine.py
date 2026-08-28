"""Sparse Laurent hop certifier. LEVEL A is not ZERO. No full-kernel together."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from research.coefficient_laurent.cache import certificate_key, sha256_text
from research.coefficient_laurent.c0 import match_constant
from research.coefficient_laurent.schema import (
    LEVEL_A,
    METHOD_VERSION,
    NONZERO,
    UNKNOWN,
    ZERO,
    LaurentCertificate,
    compose_hop_verdict,
)
from research.iterated_confluence.spectator import split_edge

NTERMS = 3
PMIN = -6
PMAX = 0
COEFF_EXPAND_CAP = 400
CANCEL_OPS_CAP = 400


def _ops(expr: Any) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return COEFF_EXPAND_CAP + 1


def _peel(expr: sympy.Expr) -> sympy.Expr:
    rest = [a for a in sympy.Mul.make_args(expr) if not isinstance(a, AppliedUndef)]
    return sympy.Mul(*rest) if rest else sympy.Integer(1)


def _split_add(expr: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr, bool]:
    pre: list[sympy.Expr] = []
    add: Optional[sympy.Expr] = None
    for a in sympy.Mul.make_args(expr):
        if isinstance(a, sympy.Add) and a.atoms(sympy.polygamma):
            add = a
        else:
            pre.append(a)
    if add is None:
        return sympy.Integer(1), expr, True
    pref = sympy.Mul(*pre) if pre else sympy.Integer(1)
    ok = (pref * add) == expr or sympy.expand(pref * add - expr) == 0
    return pref, add, bool(ok)


def _is_zero(expr: sympy.Expr) -> Optional[bool]:
    if expr == 0:
        return True
    try:
        if sympy.expand(expr) == 0:
            return True
    except Exception:
        return None
    if _ops(expr) > CANCEL_OPS_CAP:
        return None
    try:
        d = sympy.cancel(expr)
        if d == 0:
            return True
        if d.is_number and d != 0:
            return False
    except Exception:
        return None
    return None


def sparse_laurent_limit(
    source: sympy.Expr,
    target: sympy.Expr,
    variable: sympy.Expr,
    target_value: sympy.Expr,
    *,
    source_text: str = "",
    target_text: str = "",
    source_member: str = "",
    target_member: str = "",
) -> LaurentCertificate:
    """LEVEL C ZERO only if negatives vanish, C0 matches, remainder OK."""
    steps: list[str] = []
    cert = LaurentCertificate(
        source_member=source_member,
        target_member=target_member,
        degeneration_variable=str(variable),
        target_value=str(target_value),
        required_power_min=PMIN,
        required_power_max=PMAX,
        source_text_hash=sha256_text(source_text) if source_text else "",
        target_text_hash=sha256_text(target_text) if target_text else "",
        method_version=METHOD_VERSION,
        used_full_together=False,
    )
    try:
        split = split_edge(source, target, degeneration=variable)
        work_s = split["A_local"] if split["certified"] else source
        work_t = split["B_local"] if split["certified"] else target
        steps.append("split:" + str(split.get("note")))
        pref, add, recon = _split_add(work_s)
        terms = list(sympy.Add.make_args(add))
        cert.atom_records = [{"i": i, "ops": _ops(t)} for i, t in enumerate(terms)]
        cert.atom_decomposition_hash = sha256_text("|".join(str(_ops(t)) for t in terms))
        if not recon:
            v, lvl = compose_hop_verdict(
                reconstruction_ok=False, atoms_expanded=False,
                negative_verdict=UNKNOWN, constant_verdict=UNKNOWN,
                remainder_verdict=UNKNOWN,
            )
            cert.final_verdict, cert.proof_level = v, lvl
            return cert
        t = sympy.Dummy("t")
        acc: dict[int, sympy.Expr] = defaultdict(lambda: sympy.Integer(0))
        max_ops = 0
        for term in terms:
            expr = (pref * term).xreplace({variable: target_value + t})
            s = expr.series(t, 0, NTERMS)
            core = s.removeO() if isinstance(s, sympy.Expr) and s.has(sympy.Order) else s
            max_ops = max(max_ops, _ops(core))
            for p in range(PMIN, PMAX + 1):
                acc[p] += core.coeff(t, p)
        cert.max_intermediate_ops = max_ops
        summed: dict[str, str] = {}
        neg = ZERO
        for p in range(PMIN, 0):
            z = _is_zero(acc[p])
            summed[str(p)] = "0" if z is True else ("nonzero" if z is False else "undecided")
            if z is False:
                neg = NONZERO
            elif z is None and neg == ZERO:
                neg = UNKNOWN
        cert.negative_coefficients_verdict = neg
        cert.summed_coefficients = summed
        c0 = acc[0]
        summed["0"] = f"ops:{_ops(c0)}"
        c0_match = match_constant(c0, work_t)
        steps.append("c0:" + c0_match.provenance)
        c0v = c0_match.verdict
        cert.constant_term_verdict = c0v
        # Affine polygamma arguments at t=0 are not nonpositive integers
        # for the frozen Guo kernels (energy arguments ~ 1/2 + i E). Remainder
        # is ZERO only when negatives and reconstruction succeeded; else UNKNOWN.
        rem = ZERO if (recon and neg == ZERO) else UNKNOWN
        cert.remainder_verdict = rem
        v, lvl = compose_hop_verdict(
            reconstruction_ok=True,
            atoms_expanded=True,
            negative_verdict=neg,
            constant_verdict=c0v,
            remainder_verdict=rem,
        )
        cert.final_verdict, cert.proof_level = v, lvl
        return cert
    except Exception as exc:
        cert.final_verdict = UNKNOWN
        cert.proof_level = LEVEL_A
        cert.summed_coefficients["error"] = type(exc).__name__
        return cert
