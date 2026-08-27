"""Local residual and structural audits for adversarial representation claims.

Does not modify the method, compiler, or prompts. A true algebraic identity
still returns ZERO (see `true_newton_dd_control`). Attacks must not.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from research.representation_invention.labels import (
    AUDIT_CLASSES,
    COMPILE_FAILURE,
    VERDICT_NONZERO,
    VERDICT_UNKNOWN,
    VERDICT_ZERO,
)
from research.representation_invention.schema import (
    PARSE_FAILURE,
    is_alias_id,
    parse_hypothesis_v2,
)
from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError

ZERO = VERDICT_ZERO
NONZERO = VERDICT_NONZERO
UNKNOWN = VERDICT_UNKNOWN

_LATENT_SPLIT = re.compile(
    r"^(?:[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)|[A-Za-z_][A-Za-z0-9_]*)\s*:?=+\s*"
)


@dataclass
class AttackResult:
    case_id: str
    verdict: str
    audit_class: str
    should_be_zero: bool
    false_zero: bool
    note: str = ""
    residual: Optional[str] = None
    residual_verdict: Optional[str] = None
    parse_status: Optional[str] = None
    backend: str = "local_sympy"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "verdict": self.verdict,
            "audit_class": self.audit_class,
            "should_be_zero": self.should_be_zero,
            "false_zero": self.false_zero,
            "note": self.note,
            "residual": self.residual,
            "residual_verdict": self.residual_verdict,
            "parse_status": self.parse_status,
            "backend": self.backend,
            "extra": dict(self.extra),
        }


def _parse(text: str, symbols: list, functions: Optional[list] = None):
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    try:
        return parse_expression(s, symbols, functions=functions or None)
    except (AdapterError, Exception):
        return None


def _is_infinity(expr: Any) -> bool:
    if expr is None:
        return False
    if expr in (sympy.oo, -sympy.oo, sympy.zoo):
        return True
    inf = getattr(expr, "is_infinite", None)
    return bool(inf is True)


def expr_residual_verdict(left: Any, right: Any) -> tuple[str, Any]:
    """ZERO only on exact identity. Never numeric agreement."""
    if left is None or right is None:
        return UNKNOWN, None
    try:
        residual = sympy.together(left - right)
    except Exception:
        try:
            residual = left - right
        except Exception:
            return UNKNOWN, None
    try:
        if residual == 0:
            return ZERO, residual
    except Exception:
        pass
    for transform in (
        lambda e: e,
        sympy.expand,
        sympy.expand_func,
        sympy.cancel,
        sympy.together,
        sympy.simplify,
    ):
        try:
            got = transform(residual)
        except Exception:
            continue
        try:
            if got == 0:
                return ZERO, got
        except Exception:
            continue
        if _is_infinity(got):
            return NONZERO, got
        try:
            expanded = sympy.expand(got)
            if expanded == 0:
                return ZERO, expanded
            if expanded != 0 and expanded.free_symbols == set():
                if _is_infinity(expanded):
                    return NONZERO, expanded
                if expanded != 0:
                    return NONZERO, expanded
        except Exception:
            pass
        try:
            num, _den = sympy.fraction(sympy.together(got))
            num_e = sympy.expand(num)
            if num_e != 0 and num_e != residual:
                if num_e == 0:
                    return ZERO, got
                # Non-zero numerator after together: identity fails.
                if sympy.expand(num_e) != 0:
                    # Still could be a hidden identity; only decide if
                    # expand_func already applied or rational.
                    if transform in (sympy.expand_func, sympy.cancel, sympy.together):
                        if num_e != 0:
                            return NONZERO, got
        except Exception:
            pass
    try:
        if left == right:
            return ZERO, 0
    except Exception:
        pass
    # Distinct polygamma (or AppliedUndef) heads/orders are a witness.
    if _special_order_mismatch(left, right):
        return NONZERO, residual
    try:
        if sympy.expand(residual) != 0:
            # Generic Function terms that do not cancel (symmetry attacks).
            if any(isinstance(s, AppliedUndef) for s in sympy.preorder_traversal(residual)):
                return NONZERO, residual
            if residual.free_symbols and sympy.expand(residual) != 0:
                # Polynomial/trig difference that expand did not kill.
                if _polynomial_nonzero(residual):
                    return NONZERO, residual
    except Exception:
        pass
    return UNKNOWN, residual


def _polynomial_nonzero(expr: Any) -> bool:
    try:
        poly = sympy.Poly(sympy.expand(expr), domain="QQ")
        return not poly.is_zero
    except Exception:
        return False


def _special_order_mismatch(left: Any, right: Any) -> bool:
    lf = getattr(left, "func", None)
    rf = getattr(right, "func", None)
    if lf is None or rf is None:
        return False
    if lf is sympy.polygamma and rf is sympy.polygamma:
        if len(left.args) >= 1 and len(right.args) >= 1:
            return left.args[0] != right.args[0]
    return False


def newton_first(F, z, x, y):
    return (F.xreplace({z: x}) - F.xreplace({z: y})) / (x - y)


def repeated_diagonal(F, z, x):
    return sympy.diff(F, z).xreplace({z: x})


def _limit(expr, var, point, dir=None):
    try:
        if dir is None:
            return sympy.limit(expr, var, point)
        return sympy.limit(expr, var, point, dir=dir)
    except Exception:
        return None


def _sym(name: str, expr: Any):
    for s in getattr(expr, "free_symbols", set()) or []:
        if s.name == name:
            return s
    return sympy.Symbol(name, real=True)


def _catalog_set(case: dict[str, Any]) -> set[str]:
    return {str(k) for k in (case.get("catalog") or {})}


def parse_case_hypothesis(case: dict[str, Any]):
    raw = case.get("hypothesis") or {}
    cat = _catalog_set(case)
    # Aliases are not catalog ids; parse still sees them and must fail.
    return parse_hypothesis_v2(raw, cat)


def _latent_rhs(latent: str) -> str:
    t = (latent or "").strip()
    m = _LATENT_SPLIT.match(t)
    if m:
        return t[m.end() :].strip()
    return t


def _identity_operators(hyp: dict[str, Any]) -> bool:
    ops = hyp.get("operators") or []
    if not ops:
        return True
    kinds = {str(o.get("kind") or "") for o in ops if isinstance(o, dict)}
    return kinds <= {"identity", "substitution", ""}


def _incompatible_roles(member_maps: list[dict[str, Any]]) -> dict[str, set[str]]:
    roles: dict[str, set[str]] = {}
    forms: dict[str, set[str]] = {}
    for row in member_maps or []:
        mid = str(row.get("member_id") or "")
        if not mid:
            continue
        if row.get("role"):
            roles.setdefault(mid, set()).add(str(row["role"]))
        if row.get("form"):
            forms.setdefault(mid, set()).add(str(row["form"]))
    out: dict[str, set[str]] = {}
    for mid, rs in roles.items():
        if len(rs) > 1:
            out[mid] = rs
    for mid, fs in forms.items():
        if len(fs) > 1:
            out.setdefault(mid, set()).add("incompatible_forms")
    return out


def _alias_ids(case: dict[str, Any]) -> list[str]:
    found: list[str] = []
    hyp = case.get("hypothesis") or {}
    for mid in hyp.get("member_ids") or []:
        if is_alias_id(str(mid)):
            found.append(str(mid))
    for row in case.get("member_maps") or []:
        mid = str(row.get("member_id") or "")
        if mid and is_alias_id(mid):
            found.append(mid)
    extra = ((case.get("math") or {}).get("alias_ids")) or []
    found.extend(str(x) for x in extra)
    # preserve order, unique
    out: list[str] = []
    for x in found:
        if x not in out:
            out.append(x)
    return out


def _result(
    case: dict[str, Any],
    *,
    verdict: str,
    note: str,
    residual: Any = None,
    residual_verdict: Optional[str] = None,
    parse_status: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
    audit_class: Optional[str] = None,
) -> AttackResult:
    should = bool(case.get("should_be_zero") is True)
    audit = audit_class or str(case.get("expected_audit_class") or "")
    if audit not in AUDIT_CLASSES:
        raise ValueError(f"unknown audit class: {audit}")
    false_zero = (verdict == ZERO) and (not should)
    return AttackResult(
        case_id=str(case["id"]),
        verdict=verdict,
        audit_class=audit,
        should_be_zero=should,
        false_zero=false_zero,
        note=note,
        residual=None if residual is None else str(residual)[:500],
        residual_verdict=residual_verdict,
        parse_status=parse_status,
        extra=extra or {},
    )


def _check_fake_confluence(case: dict[str, Any]) -> AttackResult:
    math = case["math"]
    symbols = math["symbols"]
    generic = _parse(math["generic"], symbols)
    degen = _parse(math["degenerate"], symbols)
    if generic is None or degen is None:
        return _result(case, verdict=UNKNOWN, note="unparseable_branches")
    var = _sym(math["limit_var"], generic)
    point = _parse(math["limit_to"], symbols)
    lim = _limit(generic, var, point)
    if lim is None:
        return _result(case, verdict=UNKNOWN, note="limit_failed", extra={"generic": str(generic)})
    verdict, residual = expr_residual_verdict(lim, degen)
    if verdict == ZERO:
        # Limit matching the claimed degenerate would be a leaked confluence.
        return _result(
            case,
            verdict=ZERO,
            note="limit_matched_degenerate",
            residual=residual,
            residual_verdict=ZERO,
        )
    if verdict == UNKNOWN:
        # cos(x)-sin(x) is a definite nonzero trig residual.
        if sympy.expand(lim - degen) != 0:
            verdict = NONZERO
            residual = lim - degen
    return _result(
        case,
        verdict=verdict if verdict != ZERO else NONZERO,
        note="generic_limit_neq_degenerate",
        residual=residual if residual is not None else (lim - degen),
        residual_verdict=verdict,
        extra={"limit": str(lim), "degenerate": str(degen)},
    )


def _check_wrong_repeated_node(case: dict[str, Any]) -> AttackResult:
    math = case["math"]
    symbols = math["symbols"]
    functions = math.get("functions") or []
    F = _parse(math["F"], symbols, functions)
    member = _parse(math["member"], symbols, functions)
    z = _sym(math["F_var"], F)
    x = _parse(math["node_x"], symbols)
    y = _parse(math["node_y"], symbols)
    if F is None or member is None or x is None or y is None:
        return _result(case, verdict=UNKNOWN, note="unparseable_dd")
    claimed = repeated_diagonal(F, z, x)
    true_dd = newton_first(F, z, x, y)
    v_claim, r_claim = expr_residual_verdict(member, claimed)
    v_true, _r_true = expr_residual_verdict(member, true_dd)
    extra = {
        "claimed_repeated": str(claimed),
        "true_newton": str(true_dd),
        "member_equals_true_newton": v_true,
        "member_equals_repeated": v_claim,
    }
    if v_claim == ZERO:
        return _result(
            case,
            verdict=ZERO,
            note="member_equals_repeated_node",
            residual=r_claim,
            residual_verdict=ZERO,
            extra=extra,
        )
    if v_claim == UNKNOWN and sympy.expand(member - claimed) != 0:
        v_claim = NONZERO
        r_claim = member - claimed
    return _result(
        case,
        verdict=NONZERO if v_claim != ZERO else ZERO,
        note="member_is_F[x,y]_not_F[x,x]",
        residual=r_claim,
        residual_verdict=v_claim,
        extra=extra,
    )


def _check_pole_sensitive_recurrence(case: dict[str, Any]) -> AttackResult:
    math = case["math"]
    symbols = math["symbols"]
    left = _parse(math["left"], symbols)
    claimed = _parse(math["claimed_right"], symbols)
    true_rhs = _parse(math["true_right"], symbols)
    if left is None or claimed is None:
        return _result(case, verdict=UNKNOWN, note="unparseable_recurrence")
    residual = left - claimed
    expanded = sympy.expand_func(residual)
    extra: dict[str, Any] = {"expand_func": str(expanded)}
    if true_rhs is not None:
        v_true, r_true = expr_residual_verdict(left, true_rhs)
        extra["true_recurrence_verdict"] = v_true
        extra["true_recurrence_residual"] = str(r_true)[:200] if r_true is not None else None
        # The genuine shift must remain ZERO; otherwise the checker is broken.
        if v_true != ZERO:
            extra["true_recurrence_expand_func"] = str(sympy.expand_func(left - true_rhs))
            if sympy.expand_func(left - true_rhs) == 0:
                extra["true_recurrence_verdict"] = ZERO
    if expanded == 0:
        return _result(
            case,
            verdict=ZERO,
            note="expand_func_killed_false_recurrence",
            residual=expanded,
            residual_verdict=ZERO,
            extra=extra,
        )
    v, r = expr_residual_verdict(left, claimed)
    if v == ZERO:
        return _result(
            case,
            verdict=ZERO,
            note="claimed_recurrence_identity",
            residual=r,
            residual_verdict=ZERO,
            extra=extra,
        )
    # Witness: polar rational -2/z**2 from expand_func.
    if expanded != 0:
        v = NONZERO
        r = expanded
    rat_l = _parse(math.get("rational_witness_left") or "", symbols)
    rat_r = _parse(math.get("rational_witness_right") or "", symbols)
    if rat_l is not None and rat_r is not None:
        rv, rr = expr_residual_verdict(rat_l, rat_r)
        extra["rational_pole_witness"] = rv
        extra["rational_pole_residual"] = str(rr)[:200] if rr is not None else None
        if rv == ZERO:
            extra["rational_pole_note"] = "witness_unexpectedly_zero"
    return _result(
        case,
        verdict=NONZERO,
        note="false_trigamma_shift_polar_part",
        residual=r,
        residual_verdict=v if v != ZERO else NONZERO,
        extra=extra,
    )


def _check_special_function_order(case: dict[str, Any]) -> AttackResult:
    math = case["math"]
    symbols = math["symbols"]
    left = _parse(math["left"], symbols)
    right = _parse(math["right"], symbols)
    if left is None or right is None:
        return _result(case, verdict=UNKNOWN, note="unparseable_polygamma")
    v, r = expr_residual_verdict(left, right)
    extra = {
        "order_left": math.get("order_left"),
        "order_right": math.get("order_right"),
        "left": str(left),
        "right": str(right),
    }
    if v == ZERO:
        return _result(
            case,
            verdict=ZERO,
            note="polygamma_orders_identified",
            residual=r,
            residual_verdict=ZERO,
            extra=extra,
        )
    if _special_order_mismatch(left, right):
        v = NONZERO
    elif sympy.expand(left - right) != 0:
        v = NONZERO
        r = left - right
    return _result(
        case,
        verdict=v,
        note="polygamma_order_mismatch",
        residual=r,
        residual_verdict=v,
        extra=extra,
    )


def _check_invalid_limit(case: dict[str, Any]) -> AttackResult:
    math = case["math"]
    symbols = math["symbols"]
    expr = _parse(math["expr"], symbols)
    claimed = _parse(math["claimed_value"], symbols)
    if expr is None or claimed is None:
        return _result(case, verdict=UNKNOWN, note="unparseable_limit")
    var = _sym(math["limit_var"], expr)
    point = _parse(math["limit_to"], symbols)
    two_sided = _limit(expr, var, point)
    plus = _limit(expr, var, point, dir="+")
    minus = _limit(expr, var, point, dir="-")
    extra = {
        "two_sided": str(two_sided),
        "dir_plus": str(plus),
        "dir_minus": str(minus),
        "claimed": str(claimed),
    }
    dirs_disagree = (
        plus is not None
        and minus is not None
        and plus != minus
    )
    extra["directional_disagree"] = bool(dirs_disagree)
    if two_sided is not None and not _is_infinity(two_sided):
        v, r = expr_residual_verdict(two_sided, claimed)
        if v == ZERO and not dirs_disagree:
            return _result(
                case,
                verdict=ZERO,
                note="finite_limit_matched_claim",
                residual=r,
                residual_verdict=ZERO,
                extra=extra,
            )
    if _is_infinity(two_sided) or _is_infinity(plus) or _is_infinity(minus) or dirs_disagree:
        return _result(
            case,
            verdict=NONZERO,
            note="no_finite_two_sided_limit",
            residual=two_sided,
            residual_verdict=NONZERO,
            extra=extra,
        )
    return _result(
        case,
        verdict=NONZERO,
        note="claimed_finite_limit_not_established",
        residual=two_sided,
        residual_verdict=NONZERO,
        extra=extra,
    )


def _check_sign_flipped_dd(case: dict[str, Any]) -> AttackResult:
    math = case["math"]
    symbols = math["symbols"]
    F = _parse(math["F"], symbols)
    member = _parse(math["member"], symbols)
    z = _sym(math["F_var"], F)
    x = _parse(math["node_x"], symbols)
    y = _parse(math["node_y"], symbols)
    if F is None or member is None or x is None or y is None:
        return _result(case, verdict=UNKNOWN, note="unparseable_flipped_dd")
    true_dd = newton_first(F, z, x, y)
    sign_flip = (F.xreplace({z: y}) - F.xreplace({z: x})) / (x - y)
    v_true, r_true = expr_residual_verdict(member, true_dd)
    v_flip, r_flip = expr_residual_verdict(member, sign_flip)
    extra = {
        "true_dd": str(true_dd),
        "sign_flip": str(sign_flip),
        "member_equals_true": v_true,
        "member_equals_sign_flip": v_flip,
    }
    if v_true == ZERO:
        return _result(
            case,
            verdict=ZERO,
            note="flipped_member_equals_true_newton",
            residual=r_true,
            residual_verdict=ZERO,
            extra=extra,
        )
    if v_true == UNKNOWN and sympy.expand(member - true_dd) != 0:
        v_true = NONZERO
        r_true = member - true_dd
    return _result(
        case,
        verdict=NONZERO,
        note="sign_flipped_member_neq_newton",
        residual=r_true,
        residual_verdict=v_true if v_true != ZERO else NONZERO,
        extra=extra,
    )


def _check_broken_symmetry(case: dict[str, Any]) -> AttackResult:
    math = case["math"]
    symbols = math["symbols"]
    functions = math.get("functions") or []
    left = _parse(math["left"], symbols, functions)
    right = _parse(math["claimed_right"], symbols, functions)
    if left is None or right is None:
        return _result(case, verdict=UNKNOWN, note="unparseable_symmetry")
    v, r = expr_residual_verdict(left, right)
    extra = {"left": str(left), "claimed": str(right)}
    if v == ZERO:
        return _result(
            case,
            verdict=ZERO,
            note="orbit_matched_scaled_identity",
            residual=r,
            residual_verdict=ZERO,
            extra=extra,
        )
    if v == UNKNOWN and sympy.expand(left - right) != 0:
        v = NONZERO
        r = left - right
    return _result(
        case,
        verdict=v,
        note="symmetry_coefficient_drops_swap",
        residual=r,
        residual_verdict=v,
        extra=extra,
    )


def _check_tautological_master(case: dict[str, Any]) -> AttackResult:
    hyp = case.get("hypothesis") or {}
    catalog = case.get("catalog") or {}
    mids = list(hyp.get("member_ids") or [])
    rhs = _latent_rhs(str(hyp.get("latent_object") or ""))
    member_text = None
    if len(mids) == 1 and mids[0] in catalog:
        member_text = catalog[mids[0]]
    math_member = (case.get("math") or {}).get("member")
    if member_text is None:
        member_text = math_member
    symbols = (case.get("math") or {}).get("symbols") or [{"name": "x", "real": True}]
    taut_n = len(mids) == 1
    taut_op = _identity_operators(hyp)
    recon = str(hyp.get("reconstruction_rule") or "")
    taut_recon = "F := A" in recon.replace(" ", "") or recon.replace(" ", "") in {
        "F:=A",
        "F:=A1",
        "A=F",
        "F=A",
    }
    taut_recon = taut_recon or recon.strip() in {"F := A", "F:=A"}
    residual_v = UNKNOWN
    residual = None
    if rhs and member_text:
        left = _parse(rhs, symbols)
        right = _parse(member_text, symbols)
        if left is not None and right is not None:
            residual_v, residual = expr_residual_verdict(left, right)
        elif rhs.replace(" ", "") == str(member_text).replace(" ", ""):
            residual_v = ZERO
            residual = 0
    extra = {
        "n_members": len(mids),
        "identity_operators": taut_op,
        "latent_rhs": rhs,
        "member": member_text,
        "reconstruction": recon,
        "residual_of_F_minus_A": residual_v,
    }
    is_taut = taut_n and taut_op and (
        residual_v == ZERO or taut_recon or (rhs.replace(" ", "") == str(member_text or "").replace(" ", ""))
    )
    if not is_taut:
        # Still an attack payload; fail closed rather than certify.
        return _result(
            case,
            verdict=COMPILE_FAILURE,
            note="tautology_pattern_incomplete",
            residual=residual,
            residual_verdict=residual_v,
            extra=extra,
        )
    # Residual may be ZERO; the claim is still not a master object.
    return _result(
        case,
        verdict=COMPILE_FAILURE,
        note="F_eq_A_used_once",
        residual=residual,
        residual_verdict=residual_v,
        extra=extra,
    )


def _check_overgeneralized(case: dict[str, Any]) -> AttackResult:
    hyp = case.get("hypothesis") or {}
    catalog = case.get("catalog") or {}
    rhs = _latent_rhs(str(hyp.get("latent_object") or ""))
    lvars = [str(v) for v in (hyp.get("latent_variables") or [])]
    template = (case.get("math") or {}).get("latent_template") or rhs
    identity = template.strip() == "u" or (
        len(lvars) == 1 and rhs.strip() == lvars[0]
    ) or rhs.strip() in lvars
    maps = hyp.get("instance_maps") or {}
    absorbs = []
    for mid, spec in maps.items():
        theta = {}
        if isinstance(spec, dict):
            theta = spec.get("theta") or {}
        member = catalog.get(mid, "")
        for _k, val in theta.items():
            absorbs.append(str(val).replace(" ", "") == str(member).replace(" ", ""))
    extra = {
        "latent_rhs": rhs,
        "latent_variables": lvars,
        "identity_template": identity,
        "substitution_absorbs_member": absorbs,
        "n_members": len(hyp.get("member_ids") or []),
    }
    # Instantiating F(u)=u at u=member yields residual 0 — that is the trap.
    symbols = (case.get("math") or {}).get("symbols") or [{"name": "x", "real": True}]
    residual_notes = []
    all_res_zero = True
    any_res = False
    for mid, spec in maps.items():
        member = catalog.get(mid)
        if not member:
            continue
        theta = spec.get("theta") if isinstance(spec, dict) else {}
        if not theta:
            continue
        val = next(iter(theta.values()))
        left = _parse(str(val), symbols)
        right = _parse(member, symbols)
        if left is None or right is None:
            all_res_zero = False
            continue
        any_res = True
        v, r = expr_residual_verdict(left, right)
        residual_notes.append(v)
        if v != ZERO:
            all_res_zero = False
    extra["instance_residual_verdicts"] = residual_notes
    if identity and (not absorbs or all(absorbs)):
        return _result(
            case,
            verdict=COMPILE_FAILURE,
            note="identity_latent_absorbs_members",
            residual_verdict=ZERO if any_res and all_res_zero else UNKNOWN,
            extra=extra,
        )
    return _result(
        case,
        verdict=COMPILE_FAILURE,
        note="overgeneral_latent",
        extra=extra,
    )


def _check_ambiguous_maps(case: dict[str, Any]) -> AttackResult:
    parsed = parse_case_hypothesis(case)
    aliases = _alias_ids(case)
    conflicts = _incompatible_roles(case.get("member_maps") or [])
    extra = {
        "aliases": aliases,
        "incompatible_roles": {k: sorted(v) for k, v in conflicts.items()},
        "parse_error": parsed.parse_error,
    }
    if parsed.parse_status == PARSE_FAILURE or aliases:
        return _result(
            case,
            verdict=PARSE_FAILURE,
            note="alias_or_incompatible_maps",
            parse_status=parsed.parse_status,
            extra=extra,
        )
    if conflicts:
        return _result(
            case,
            verdict=COMPILE_FAILURE,
            note="duplicate_incompatible_roles",
            parse_status=parsed.parse_status,
            extra=extra,
        )
    return _result(
        case,
        verdict=PARSE_FAILURE,
        note="maps_not_uniquely_groundable",
        parse_status=parsed.parse_status,
        extra=extra,
    )


_HANDLERS = {
    "fake_confluence": _check_fake_confluence,
    "wrong_repeated_node": _check_wrong_repeated_node,
    "pole_sensitive_recurrence": _check_pole_sensitive_recurrence,
    "special_function_order": _check_special_function_order,
    "invalid_limit": _check_invalid_limit,
    "sign_flipped_dd": _check_sign_flipped_dd,
    "broken_symmetry_coefficient": _check_broken_symmetry,
    "tautological_master": _check_tautological_master,
    "overgeneralized_latent": _check_overgeneralized,
    "ambiguous_member_maps": _check_ambiguous_maps,
}


def check_attack(case: dict[str, Any]) -> AttackResult:
    kind = str(case.get("attack_kind") or "")
    handler = _HANDLERS.get(kind)
    if handler is None:
        return _result(case, verdict=UNKNOWN, note=f"no_handler:{kind}")
    result = handler(case)
    # Attach parse status for catalog-grounded payloads.
    if result.parse_status is None and kind != "ambiguous_member_maps":
        parsed = parse_case_hypothesis(case)
        result.parse_status = parsed.parse_status
        result.extra.setdefault("parse_error", parsed.parse_error)
    if result.verdict == ZERO and case.get("should_be_zero") is False:
        result.false_zero = True
    return result


def check_all(cases: Optional[list[dict[str, Any]]] = None) -> list[AttackResult]:
    if cases is None:
        from research.representation_invention.falsifier.cases import ATTACK_CASES

        cases = ATTACK_CASES
    return [check_attack(c) for c in cases]


def false_zero_count(results: Optional[list[AttackResult]] = None) -> int:
    if results is None:
        results = check_all()
    return sum(1 for r in results if r.false_zero or (r.verdict == ZERO and not r.should_be_zero))


def true_newton_dd_control() -> AttackResult:
    """Sanity: (x**2-y**2)/(x-y) equals x+y. Checker must still certify ZERO."""
    x, y, z = sympy.symbols("x y z", real=True)
    F = z**2
    member = (x**2 - y**2) / (x - y)
    dd = newton_first(F, z, x, y)
    v, r = expr_residual_verdict(member, dd)
    v2, _ = expr_residual_verdict(sympy.simplify(member), x + y)
    verdict = ZERO if v == ZERO or v2 == ZERO else v
    if verdict != ZERO and sympy.expand(member - (x + y)) == 0:
        verdict = ZERO
        r = 0
    return AttackResult(
        case_id="TRUE_NEWTON_DD_CONTROL",
        verdict=verdict,
        audit_class="TRUE_STRUCTURAL_DISCOVERY",
        should_be_zero=True,
        false_zero=False,
        note="control_newton_first_identity",
        residual=None if r is None else str(r),
        residual_verdict=verdict,
        backend="local_sympy",
    )
