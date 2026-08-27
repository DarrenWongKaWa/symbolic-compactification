"""Verify compiled obligations. UNKNOWN is not success. No promotion."""
from __future__ import annotations

from typing import Optional

import sympy

from research.llm_abstraction.constructor import (
    _diff_repeat,
    _equal,
    _swap_applied,
    _swap_two_symbols,
    _sym_named,
    instantiate,
    parse_flex,
)
from research.obligation_ir.schema import (
    COMPILE_FAILURE,
    CONFLUENCE,
    DERIVATIVE,
    DIVIDED_DIFFERENCE,
    EQUALITY,
    LIMIT,
    Obligation,
    PERMUTATION,
    SUBSTITUTION,
    VerifyResult,
)
from symbolic_compactification import NONZERO, UNKNOWN, ZERO


def _verdict(member: str, cand, symbols, functions) -> str:
    mem = parse_flex(member, symbols, functions)
    if mem is None or cand is None:
        return UNKNOWN
    if _equal(mem, cand):
        return ZERO
    return NONZERO


def verify_obligation(
    obl: Obligation,
    *,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> VerifyResult:
    symbols = symbols or []
    functions = functions or []
    if obl.compile_status == COMPILE_FAILURE:
        return VerifyResult(
            kind=obl.kind,
            verdict=UNKNOWN,
            backend="none",
            note=obl.compile_error or "compile_failure",
            compile_status=COMPILE_FAILURE,
        )
    tmpl = parse_flex(obl.latent, symbols, functions)
    if tmpl is None:
        return VerifyResult(obl.kind, UNKNOWN, "parse", "unparseable_latent")
    inst = instantiate(tmpl, obl.theta, symbols, functions)
    if obl.kind in {EQUALITY, SUBSTITUTION, CONFLUENCE}:
        v = _verdict(obl.member, inst, symbols, functions)
        return VerifyResult(obl.kind, v, "sympy_identity", "instantiate", witness=str(inst))
    if obl.kind == PERMUTATION:
        cands = [inst, _swap_applied(inst) if inst is not None else None]
        keys = list(obl.theta)
        if inst is not None:
            cands.append(_swap_two_symbols(inst, keys))
        for c in cands:
            v = _verdict(obl.member, c, symbols, functions)
            if v == ZERO:
                return VerifyResult(PERMUTATION, ZERO, "sympy_permute", "arg_or_symbol_swap", witness=str(c))
        return VerifyResult(PERMUTATION, NONZERO if inst is not None else UNKNOWN, "sympy_permute", "no_swap_match")
    if obl.kind == DERIVATIVE:
        var = _sym_named(tmpl, obl.var) if obl.var else None
        if var is None:
            for k in obl.theta:
                var = _sym_named(tmpl, k)
                if var is not None:
                    break
        if var is None and tmpl.free_symbols:
            var = next(iter(tmpl.free_symbols))
        if var is None:
            return VerifyResult(DERIVATIVE, UNKNOWN, "sympy.diff", "no_diff_variable")
        d = _diff_repeat(tmpl, var, obl.order or 1)
        d_inst = instantiate(d, obl.theta, symbols, functions)
        v = _verdict(obl.member, d_inst, symbols, functions)
        return VerifyResult(DERIVATIVE, v, "sympy.diff", f"order={obl.order}", witness=str(d_inst))
    if obl.kind == LIMIT:
        # Only when both sides parse. Engine has no general limit residual.
        left = parse_flex(obl.left, symbols, functions)
        right = parse_flex(obl.right, symbols, functions) if obl.right else None
        if left is None or right is None or not obl.var:
            return VerifyResult(LIMIT, UNKNOWN, "sympy.limit", "limit_not_grounded")
        x = _sym_named(left, obl.var) or _sym_named(right, obl.var)
        pt = parse_flex(obl.to, symbols, functions) if obl.to else None
        if x is None or pt is None:
            return VerifyResult(LIMIT, UNKNOWN, "sympy.limit", "limit_var_unbound")
        try:
            lim = sympy.limit(left, x, pt)
            if _equal(lim, right):
                return VerifyResult(LIMIT, ZERO, "sympy.limit", "limit_identity")
            return VerifyResult(LIMIT, NONZERO, "sympy.limit", "limit_mismatch")
        except Exception:
            return VerifyResult(LIMIT, UNKNOWN, "sympy.limit", "limit_engine_failed")
    if obl.kind == DIVIDED_DIFFERENCE:
        # Two-node Newton form if F, x, y all parse: (F(x)-F(y))/(x-y)
        if len(obl.nodes) < 2:
            return VerifyResult(DIVIDED_DIFFERENCE, UNKNOWN, "none", "need_two_nodes")
        return VerifyResult(DIVIDED_DIFFERENCE, UNKNOWN, "none", "dd_not_grounded_in_source")
    return VerifyResult(obl.kind, UNKNOWN, "none", "kind_not_discharged")
