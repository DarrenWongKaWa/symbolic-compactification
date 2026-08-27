"""Verify compiled experimental obligations.

UNKNOWN is returned only for a compiled (COMPILE_OK) obligation that cannot
be decided. Compile failures do not become UNKNOWN or ZERO.
"""
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
from research.representation_invention.obligations.constructors import (
    dd_backend_name,
    hermite_nodes,
    newton_first,
    parse_latent,
    take_limit,
)
from research.representation_invention.obligations.schema import (
    CompileResult,
    BASIS_RECONSTRUCTION,
    COMPILE_FAILURE,
    COMPILE_OK,
    CONFLUENCE,
    DERIVATIVE,
    EQUALITY,
    HERMITE_DD,
    LIMIT,
    MASTER_INSTANCE,
    NEWTON_DD,
    NONZERO,
    PERMUTATION,
    RECURRENCE,
    SUBSTITUTION,
    UNKNOWN,
    ZERO,
    Obligation,
    VerifyResult,
)
from symbolic_compactification import NONZERO as ENG_NONZERO
from symbolic_compactification import UNKNOWN as ENG_UNKNOWN
from symbolic_compactification import ZERO as ENG_ZERO

assert ZERO == ENG_ZERO and NONZERO == ENG_NONZERO and UNKNOWN == ENG_UNKNOWN


def verify_compiled(
    compiled: CompileResult,
    *,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> list[VerifyResult]:
    """Verify each obligation. Compile failures keep verdict=None."""
    return [
        verify_obligation(o, symbols=symbols, functions=functions)
        for o in compiled.obligations
    ]


def verify_hypothesis_v2(
    compiled: CompileResult,
    *,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> dict:
    rows = verify_compiled(compiled, symbols=symbols, functions=functions)
    return {
        "compile_status": compiled.compile_status,
        "obligations": [r.to_dict() for r in rows],
        "verdicts": [r.verdict for r in rows if r.verdict],
        "results": rows,
    }


def verify_obligation(
    obl: Obligation,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> VerifyResult:
    symbols = list(symbols or [])
    functions = list(functions or [])
    if obl.compile_status != COMPILE_OK:
        return VerifyResult(
            kind=obl.kind,
            verdict=None,
            backend="none",
            note=obl.compile_error or "compile_failure",
            compile_status=COMPILE_FAILURE,
        )
    dispatch = {
        NEWTON_DD: _v_newton,
        HERMITE_DD: _v_hermite,
        CONFLUENCE: _v_limit,
        LIMIT: _v_limit,
        DERIVATIVE: _v_derivative,
        SUBSTITUTION: _v_instantiate,
        EQUALITY: _v_equality,
        PERMUTATION: _v_permutation,
        RECURRENCE: _v_recurrence,
        MASTER_INSTANCE: _v_master,
        BASIS_RECONSTRUCTION: _v_basis,
    }
    fn = dispatch.get(obl.kind)
    if fn is None:
        return VerifyResult(obl.kind, UNKNOWN, "none", "kind_not_discharged", COMPILE_OK)
    return fn(obl, symbols, functions)


def _cmp(
    mem: Optional[sympy.Expr],
    cand: Optional[sympy.Expr],
    kind: str,
    backend: str,
    note: str,
) -> VerifyResult:
    if mem is None or cand is None:
        return VerifyResult(kind, UNKNOWN, backend, "unparseable_side", COMPILE_OK)
    if _equal(mem, cand):
        return VerifyResult(kind, ZERO, backend, note, COMPILE_OK, witness=str(cand))
    return VerifyResult(kind, NONZERO, backend, note or "mismatch", COMPILE_OK, witness=str(cand))


def _parse_F(obl: Obligation, symbols, functions):
    return parse_latent(obl.latent, None, symbols, functions)


def _v_newton(obl: Obligation, symbols, functions) -> VerifyResult:
    backend = dd_backend_name()
    F, z, _ = _parse_F(obl, symbols, functions)
    if F is None or z is None or len(obl.nodes) < 2:
        return VerifyResult(NEWTON_DD, UNKNOWN, backend, "newton_rebuild_failed", COMPILE_OK)
    x = parse_flex(obl.nodes[0], symbols, functions)
    y = parse_flex(obl.nodes[1], symbols, functions)
    mem = parse_flex(obl.left, symbols, functions)
    if x is None or y is None:
        return VerifyResult(NEWTON_DD, UNKNOWN, backend, "unparseable_nodes", COMPILE_OK)
    cand = newton_first(F, z, x, y)
    return _cmp(mem, cand, NEWTON_DD, backend, "newton_first")


def _v_hermite(obl: Obligation, symbols, functions) -> VerifyResult:
    backend = dd_backend_name()
    F, z, _ = _parse_F(obl, symbols, functions)
    if F is None or z is None or len(obl.nodes) < 1:
        return VerifyResult(HERMITE_DD, UNKNOWN, backend, "hermite_rebuild_failed", COMPILE_OK)
    parsed = [parse_flex(n, symbols, functions) for n in obl.nodes]
    if any(p is None for p in parsed):
        return VerifyResult(HERMITE_DD, UNKNOWN, backend, "unparseable_nodes", COMPILE_OK)
    cand = hermite_nodes(F, z, parsed)
    mem = parse_flex(obl.left, symbols, functions)
    return _cmp(mem, cand, HERMITE_DD, backend, "hermite_nodes")


def _limit_var(expr: sympy.Expr, var_text: str, symbols, functions):
    named = _sym_named(expr, var_text)
    if named is not None:
        return named
    parsed = parse_flex(var_text, symbols, functions)
    return parsed


def _v_limit(obl: Obligation, symbols, functions) -> VerifyResult:
    generic = parse_flex(obl.left, symbols, functions)
    target = parse_flex(obl.right, symbols, functions)
    if generic is None or target is None or not obl.var or not obl.to:
        return VerifyResult(obl.kind, UNKNOWN, "sympy.limit", "limit_not_grounded", COMPILE_OK)
    var = _limit_var(generic, obl.var, symbols, functions)
    pt = parse_flex(obl.to, symbols, functions)
    if var is None or pt is None:
        return VerifyResult(obl.kind, UNKNOWN, "sympy.limit", "limit_var_unbound", COMPILE_OK)
    try:
        lim = take_limit(generic, var, pt)
    except Exception as exc:
        return VerifyResult(
            obl.kind, UNKNOWN, "sympy.limit", f"limit_engine_failed:{type(exc).__name__}", COMPILE_OK,
        )
    if lim.has(sympy.Limit) or isinstance(lim, sympy.Limit):
        return VerifyResult(obl.kind, UNKNOWN, "sympy.limit", "limit_unevaluated", COMPILE_OK)
    if getattr(lim, "is_finite", None) is False and lim in {sympy.zoo, sympy.nan}:
        return VerifyResult(obl.kind, UNKNOWN, "sympy.limit", "limit_indeterminate", COMPILE_OK)
    note = "confluence_limit" if obl.kind == CONFLUENCE else "limit_identity"
    return _cmp(lim, target, obl.kind, "sympy.limit", note)


def _v_derivative(obl: Obligation, symbols, functions) -> VerifyResult:
    F, z, _ = _parse_F(obl, symbols, functions)
    if F is None:
        return VerifyResult(DERIVATIVE, UNKNOWN, "sympy.diff", "unparseable_latent", COMPILE_OK)
    var = _sym_named(F, obl.var) if obl.var else z
    if var is None and z is not None:
        var = z
    if var is None and F.free_symbols:
        var = next(iter(F.free_symbols))
    if var is None:
        return VerifyResult(DERIVATIVE, UNKNOWN, "sympy.diff", "no_diff_variable", COMPILE_OK)
    d = _diff_repeat(F, var, obl.order or 1)
    inst = instantiate(d, obl.theta, symbols, functions)
    mem = parse_flex(obl.left, symbols, functions)
    return _cmp(mem, inst, DERIVATIVE, "sympy.diff", f"order={obl.order}")


def _v_instantiate(obl: Obligation, symbols, functions) -> VerifyResult:
    F, _z, _ = _parse_F(obl, symbols, functions)
    if F is None:
        return VerifyResult(obl.kind, UNKNOWN, "parse", "unparseable_latent", COMPILE_OK)
    inst = instantiate(F, obl.theta, symbols, functions)
    mem = parse_flex(obl.left, symbols, functions)
    return _cmp(mem, inst, obl.kind, "sympy_identity", "instantiate")


def _v_equality(obl: Obligation, symbols, functions) -> VerifyResult:
    left = parse_flex(obl.left, symbols, functions)
    if obl.latent:
        F, _z, _ = _parse_F(obl, symbols, functions)
        if F is not None:
            inst = instantiate(F, obl.theta, symbols, functions)
            if inst is not None and (not obl.right or len(obl.member_ids) < 2):
                return _cmp(left, inst, EQUALITY, "sympy_identity", "equality_instantiate")
    right = parse_flex(obl.right, symbols, functions)
    return _cmp(left, right, EQUALITY, "sympy_identity", "equality")


def _v_permutation(obl: Obligation, symbols, functions) -> VerifyResult:
    F, _z, _ = _parse_F(obl, symbols, functions)
    if F is None:
        return VerifyResult(PERMUTATION, UNKNOWN, "sympy_permute", "unparseable_latent", COMPILE_OK)
    inst = instantiate(F, obl.theta, symbols, functions)
    mem = parse_flex(obl.left, symbols, functions)
    # Unpermuted instantiate is not a candidate: otherwise identity members false-ZERO.
    cands = []
    if inst is not None:
        cands.append(_swap_applied(inst))
        cands.append(_swap_two_symbols(inst, list(obl.theta)))
        cands.append(instantiate(_swap_applied(F), obl.theta, symbols, functions))
        cands.append(instantiate(_swap_two_symbols(F, list(obl.theta)), obl.theta, symbols, functions))
    saw_nz = False
    last = None
    for c in cands:
        if c is None:
            continue
        last = c
        if mem is None:
            return VerifyResult(PERMUTATION, UNKNOWN, "sympy_permute", "unparseable_member", COMPILE_OK)
        if _equal(mem, c):
            return VerifyResult(PERMUTATION, ZERO, "sympy_permute", "arg_or_symbol_swap", COMPILE_OK, witness=str(c))
        saw_nz = True
    if saw_nz:
        return VerifyResult(PERMUTATION, NONZERO, "sympy_permute", "no_swap_match", COMPILE_OK, witness=str(last))
    return VerifyResult(PERMUTATION, UNKNOWN, "sympy_permute", "no_candidate", COMPILE_OK)


def _v_recurrence(obl: Obligation, symbols, functions) -> VerifyResult:
    F, z, _ = _parse_F(obl, symbols, functions)
    if F is None:
        return VerifyResult(RECURRENCE, UNKNOWN, "sympy_identity", "unparseable_latent", COMPILE_OK)
    if obl.left:
        mem = parse_flex(obl.left, symbols, functions)
        inst = instantiate(F, obl.theta, symbols, functions)
        if mem is not None and inst is not None and not _equal(mem, inst) and not _equal(mem, F):
            return VerifyResult(
                RECURRENCE, NONZERO, "sympy_identity", "member_not_latent", COMPILE_OK, witness=str(inst),
            )
    svar = obl.shift_var or obl.var or (z.name if z is not None else "")
    n = _sym_named(F, svar) if svar else z
    if n is None:
        n = z
    step = parse_flex(obl.shift_step or "1", symbols, functions)
    rhs = parse_flex(obl.recurrence_rhs, symbols, functions) if obl.recurrence_rhs else sympy.Integer(0)
    if n is None or step is None or rhs is None:
        return VerifyResult(RECURRENCE, UNKNOWN, "sympy_identity", "recurrence_rebuild_failed", COMPILE_OK)
    residual = F.xreplace({n: n + step}) - F - rhs
    if _equal(residual, sympy.Integer(0)):
        return VerifyResult(
            RECURRENCE, ZERO, "sympy_identity", "recurrence_zero", COMPILE_OK, witness=str(residual),
        )
    return VerifyResult(
        RECURRENCE, NONZERO, "sympy_identity", "recurrence_mismatch", COMPILE_OK, witness=str(residual),
    )


def _v_master(obl: Obligation, symbols, functions) -> VerifyResult:
    F, z, _ = _parse_F(obl, symbols, functions)
    if F is None:
        return VerifyResult(MASTER_INSTANCE, UNKNOWN, "parse", "unparseable_latent", COMPILE_OK)
    op = (obl.operator or "identity").lower()
    theta = obl.theta
    cand = None
    if op in {"identity", "substitution", "other", ""}:
        cand = instantiate(F, theta, symbols, functions)
    elif op == "derivative":
        var = z or (_sym_named(F, obl.var) if obl.var else None)
        if var is None:
            return VerifyResult(MASTER_INSTANCE, UNKNOWN, "sympy.diff", "no_diff_variable", COMPILE_OK)
        cand = instantiate(_diff_repeat(F, var, obl.order or 1), theta, symbols, functions)
    elif op == "permutation":
        inst = instantiate(F, theta, symbols, functions)
        cand = _swap_applied(inst) if inst is not None else None
    elif op == "newton_dd":
        if z is None or len(obl.nodes) < 2:
            return VerifyResult(MASTER_INSTANCE, UNKNOWN, dd_backend_name(), "need_two_nodes", COMPILE_OK)
        x = parse_flex(obl.nodes[0], symbols, functions)
        y = parse_flex(obl.nodes[1], symbols, functions)
        if x is None or y is None:
            return VerifyResult(MASTER_INSTANCE, UNKNOWN, dd_backend_name(), "unparseable_nodes", COMPILE_OK)
        cand = newton_first(F, z, x, y)
    else:
        cand = instantiate(F, theta, symbols, functions)
    mem = parse_flex(obl.left, symbols, functions)
    return _cmp(mem, cand, MASTER_INSTANCE, "sympy_identity", f"master:{op}")


def _v_basis(obl: Obligation, symbols, functions) -> VerifyResult:
    if not obl.basis or not obl.coefficients:
        return VerifyResult(
            BASIS_RECONSTRUCTION, UNKNOWN, "sympy_identity", "basis_rebuild_failed", COMPILE_OK,
        )
    acc = None
    for b in obl.basis:
        be = parse_flex(str(b), symbols, functions)
        ce = parse_flex(str(obl.coefficients.get(str(b), "0")), symbols, functions)
        if be is None or ce is None:
            return VerifyResult(
                BASIS_RECONSTRUCTION, UNKNOWN, "parse", "unparseable_basis", COMPILE_OK,
            )
        if obl.theta:
            be = instantiate(be, obl.theta, symbols, functions)
            if be is None:
                return VerifyResult(
                    BASIS_RECONSTRUCTION, UNKNOWN, "parse", "basis_instantiate_failed", COMPILE_OK,
                )
        term = ce * be
        acc = term if acc is None else acc + term
    mem = parse_flex(obl.left, symbols, functions)
    return _cmp(mem, acc, BASIS_RECONSTRUCTION, "sympy_identity", "basis_sum")
