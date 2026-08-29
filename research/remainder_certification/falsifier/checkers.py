"""Attack remainder CERTIFIED. Do not improve schema or sibling certifiers.

Local analytic-domain and order-algebra checks fill remainder verdicts.
``schema.validate_certificate`` never upgrades and forbids CERTIFIED on
class C/D. Hop composition is ``schema.compose_hop_verdict`` only.
If ``compile_remainder`` is importable it is probed; CERTIFIED on an
attack is a false certificate.
"""
from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import dataclass, field, fields
from typing import Any, Optional

import sympy

from research.coefficient_laurent.schema import UNKNOWN as HOP_UNKNOWN
from research.coefficient_laurent.schema import ZERO as HOP_ZERO
from research.coefficient_laurent.schema import compose_hop_verdict
from research.remainder_certification.falsifier.cases import (
    ATTACK_CASES,
    CONTROL_CASES,
    is_class_c_or_d,
    load_all_cases,
)
from research.remainder_certification.schema import (
    ASSUMPTION_REQUIRED,
    CERTIFIED,
    METHOD_VERSION,
    NEIGHBORHOOD_ASSUMPTION,
    NEIGHBORHOOD_CERTIFIED,
    NEIGHBORHOOD_UNKNOWN,
    NONANALYTIC,
    REMAINDER_VERDICTS,
    RemainderCertificate,
    UNKNOWN,
    validate_certificate,
)

_COMPILER_MODULES = (
    "research.remainder_certification.compiler",
    "research.remainder_certification.compiler.compile",
    "research.remainder_certification.compiler.remainder",
    "research.remainder_certification.compiler.certify",
    "research.remainder_certification.compile",
)

_PARSE_LOCAL = {
    "polygamma": sympy.polygamma,
    "PolyGamma": sympy.polygamma,
    "exp": sympy.exp,
    "log": sympy.log,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "gamma": sympy.gamma,
    "pi": sympy.pi,
    "I": sympy.I,
    "E": sympy.E,
    "oo": sympy.oo,
    "Rational": sympy.Rational,
    "Integer": sympy.Integer,
}

_RANK = {
    NONANALYTIC: 3,
    ASSUMPTION_REQUIRED: 2,
    UNKNOWN: 1,
    CERTIFIED: 0,
}


@dataclass
class CaseResult:
    case_id: str
    kind: str
    expect: str
    got: str
    false_certified: bool
    schema_verdict: str
    local_verdict: str
    compiler_verdict: Optional[str]
    hop_verdict: Optional[str]
    hop_level: Optional[str]
    trap_ignore_remainder: Optional[str]
    class_c: bool
    extra: dict[str, Any] = field(default_factory=dict)
    certificate: Optional[RemainderCertificate] = None

    def row(self) -> dict[str, str]:
        return {"id": self.case_id, "expect": self.expect, "got": self.got}


def forbidden_ignore_remainder(
    *,
    negative_verdict: str,
    constant_verdict: str,
    remainder_verdict: str | None = None,
) -> str:
    """Forbidden composer: vanished poles and t^0 skip remainder."""
    del remainder_verdict
    if negative_verdict == "NONZERO" or constant_verdict == "NONZERO":
        return "NONZERO"
    if negative_verdict == HOP_ZERO:
        return HOP_ZERO
    return HOP_UNKNOWN


def discover_compile_remainder() -> Any | None:
    for name in _COMPILER_MODULES:
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        fn = getattr(mod, "compile_remainder", None)
        if callable(fn):
            return fn
    try:
        pkg = importlib.import_module("research.remainder_certification")
    except Exception:
        return None
    fn = getattr(pkg, "compile_remainder", None)
    return fn if callable(fn) else None


def claimed_certificate(case: dict[str, Any]) -> RemainderCertificate:
    """Naive claimed remainder IR (may allege CERTIFIED)."""
    return RemainderCertificate(
        function_family=str(case.get("function_family") or ""),
        function_order=str(case.get("function_order") or ""),
        argument=str(case.get("argument") or ""),
        expansion_point=str(case.get("expansion_point") or ""),
        perturbation=str(case.get("perturbation") or ""),
        expansion_order=case.get("expansion_order"),
        domain_conditions=list(case.get("domain_conditions") or []),
        analyticity_certificate=dict(case.get("analyticity_certificate") or {}),
        distance_to_singularity=str(case.get("distance_to_singularity") or ""),
        remainder_form=str(case.get("remainder_form") or ""),
        bound=str(case.get("bound") or ""),
        required_small_t_condition=str(case.get("required_small_t_condition") or ""),
        assumptions_used=list(case.get("assumptions_used") or []),
        proof_dependencies=list(case.get("proof_dependencies") or []),
        verdict=str(case.get("claimed_verdict") or UNKNOWN),
        neighborhood_verdict=str(case.get("neighborhood_verdict") or UNKNOWN),
        assumptions_hash=_hash_assumptions(case.get("assumptions_used") or []),
        argument_text_hash=_sha(str(case.get("argument") or "")),
        method_version=METHOD_VERSION,
        note=str(case.get("trap") or ""),
    )


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_assumptions(items: list[Any]) -> str:
    try:
        blob = json.dumps(items, sort_keys=True, default=str)
    except Exception:
        blob = str(items)
    return _sha(blob)


def _as_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        n = sympy.Integer(value)
        if n == value:
            return int(n)
    except Exception:
        return None
    return None


def _symbol_from_spec(spec: Any) -> sympy.Symbol:
    if isinstance(spec, str):
        return sympy.Symbol(spec)
    name = str(spec["name"])
    kwargs: dict[str, Any] = {}
    if spec.get("real") is True:
        kwargs["real"] = True
    if spec.get("positive") is True:
        kwargs["positive"] = True
    if spec.get("integer") is True:
        kwargs["integer"] = True
    return sympy.Symbol(name, **kwargs)


def _locals(case: dict[str, Any]) -> dict[str, Any]:
    loc = dict(_PARSE_LOCAL)
    for spec in case.get("symbols") or []:
        sym = _symbol_from_spec(spec)
        loc[str(sym.name)] = sym
    tname = str(case.get("degeneration_variable") or "t")
    if tname not in loc:
        loc[tname] = sympy.Symbol(tname)
    return loc


def _parse(text: Any, case: dict[str, Any]) -> Any:
    if text is None or text == "":
        return None
    if isinstance(text, sympy.Basic):
        return text
    try:
        out = sympy.parse_expr(str(text), local_dict=_locals(case), evaluate=True)
    except Exception:
        return None
    return out if isinstance(out, sympy.Basic) else None


def _t_symbol(case: dict[str, Any]) -> sympy.Symbol:
    loc = _locals(case)
    name = str(case.get("degeneration_variable") or "t")
    sym = loc.get(name)
    return sym if isinstance(sym, sympy.Symbol) else sympy.Symbol(name)


def _family_has_poles(family: str, order: int | None) -> bool:
    if family == "exp":
        return False
    if family == "polygamma":
        if order is not None and order <= -2:
            return False
        return True
    return True


def _nonpositive_integer_kind(z0: Any) -> str:
    if z0 is None:
        return "unknown"
    try:
        z0 = sympy.simplify(sympy.expand(z0))
    except Exception:
        return "unknown"
    frees = getattr(z0, "free_symbols", set()) or set()
    if frees:
        return "unknown"
    if z0 in (sympy.nan, sympy.zoo, sympy.oo, sympy.S.NegativeInfinity):
        return "unknown"
    try:
        re_z = sympy.simplify(sympy.re(z0))
        im_z = sympy.simplify(sympy.im(z0))
    except Exception:
        return "unknown"
    if getattr(im_z, "free_symbols", set()) or getattr(re_z, "free_symbols", set()):
        return "unknown"
    if im_z != 0 and im_z.is_zero is not True:
        if isinstance(im_z, (sympy.Float, float)):
            return "unknown"
        if im_z.is_number and im_z != 0:
            return "regular"
        if im_z.is_zero is False:
            return "regular"
        return "unknown"
    x = re_z
    if isinstance(x, (sympy.Float, float)):
        return "unknown"
    if isinstance(x, sympy.Integer) or x.is_Integer is True:
        try:
            return "pole" if int(x) <= 0 else "regular"
        except Exception:
            return "unknown"
    if x.is_rational is True:
        try:
            q = int(x.q)
            if q != 1:
                return "regular"
            return "pole" if int(x.p) <= 0 else "regular"
        except Exception:
            return "unknown"
    return "unknown"


def _classify_z0(
    z0: Any,
    family: str,
    order: int | None,
    case: dict[str, Any],
    t_sym: sympy.Symbol,
) -> str:
    if family == "exp":
        return "regular"
    if family == "polygamma":
        if order is not None and order <= -2:
            return "regular"
        return _nonpositive_integer_kind(z0)
    if family == "log":
        if z0 is None:
            return "unknown"
        if getattr(z0, "free_symbols", set()):
            return "unknown"
        try:
            if z0 == 0:
                return "pole"
            if z0.is_number and z0 != 0:
                return "regular"
        except Exception:
            return "unknown"
        return "unknown"
    if family == "rational":
        if _denominator_vanishes(case, t_sym):
            return "pole"
        if z0 is None:
            return "unknown"
        if getattr(z0, "free_symbols", set()):
            return "unknown"
        return "regular"
    return "unknown"


def _affine_coeffs(z: Any, t: sympy.Symbol) -> tuple[Any, Any] | None:
    if z is None or t is None:
        return None
    try:
        expr = sympy.expand(z)
        if not expr.has(t):
            return (expr, sympy.Integer(0))
        poly = sympy.Poly(expr, t, domain=sympy.EX)
        if poly.degree() > 1:
            return None
        beta = poly.nth(1) if poly.degree() >= 1 else sympy.Integer(0)
        alpha = poly.nth(0)
        if alpha.has(t) or beta.has(t):
            return None
        return (alpha, beta)
    except Exception:
        return None


def _arbitrarily_close_pole(z0: Any, c: Any, family: str, order: int | None) -> bool:
    if not _family_has_poles(family, order):
        return False
    if z0 is not None and getattr(z0, "free_symbols", set()):
        return True
    if c is not None and getattr(c, "free_symbols", set()):
        return True
    return False


def _distance_value(z0: Any, family: str, order: int | None) -> Any:
    if family == "exp":
        return sympy.oo
    if family == "polygamma":
        if order is not None and order <= -2:
            return sympy.oo
        kind = _nonpositive_integer_kind(z0)
        if kind == "pole":
            return sympy.Integer(0)
        if kind == "unknown":
            return None
        try:
            zc = complex(z0)
        except Exception:
            return None
        best = None
        for k in range(0, 80):
            d = abs(zc + k)
            if best is None or d < best:
                best = d
        return sympy.Float(best) if best is not None else None
    if family == "log":
        try:
            if z0 is None or getattr(z0, "free_symbols", set()):
                return None
            return sympy.Abs(z0)
        except Exception:
            return None
    return None


def _denominator_vanishes(case: dict[str, Any], t_sym: sympy.Symbol) -> bool:
    den_txt = case.get("denominator")
    if not den_txt:
        return False
    den = _parse(den_txt, case)
    if den is None:
        return True
    num = _parse(case.get("numerator"), case) if case.get("numerator") else None
    try:
        d0 = sympy.expand(den.subs(t_sym, 0))
        if d0 != 0:
            return False
        if num is None:
            return True
        n0 = sympy.expand(num.subs(t_sym, 0))
        return n0 != 0
    except Exception:
        return True


def _complex_perturbation(case: dict[str, Any]) -> bool:
    if case.get("perturbation_complex"):
        return True
    pert = str(case.get("perturbation") or "")
    if "I*" in pert or pert == "I" or pert.startswith("I*") or "*I" in pert:
        return True
    tname = str(case.get("degeneration_variable") or "t")
    for spec in case.get("symbols") or []:
        if not isinstance(spec, dict):
            continue
        if spec.get("name") != tname:
            continue
        if spec.get("real") is False or spec.get("complex") is True:
            return True
    return False


def _real_only_assumption(case: dict[str, Any]) -> bool:
    if case.get("real_only_assumption"):
        return True
    for item in case.get("assumptions_used") or []:
        if not isinstance(item, dict):
            continue
        pred = str(item.get("predicate") or "").lower()
        if "real" in pred:
            return True
    return False


def _bound_contains_singularity(case: dict[str, Any], dist: Any) -> bool:
    radius = case.get("bound_radius")
    if radius is None:
        return False
    if dist is None:
        return True
    try:
        if dist == sympy.oo:
            return False
        return float(sympy.N(dist)) <= float(radius)
    except Exception:
        return True


def _symbolic_M_unproved(case: dict[str, Any]) -> bool:
    m_name = str(case.get("M_symbol") or "")
    if not m_name:
        return False
    if case.get("M_finiteness_proved"):
        return False
    key = m_name.lower()
    for dep in case.get("proof_dependencies") or []:
        text = str(dep).lower()
        if key in text and ("finite" in text or "< oo" in text or "<oo" in text):
            return False
    return True


def _combine(defects: list[tuple[str, str]]) -> tuple[str, list[str]]:
    if not defects:
        return CERTIFIED, []
    verdict = CERTIFIED
    rank = 0
    reasons: list[str] = []
    for v, reason in defects:
        reasons.append(reason)
        r = _RANK.get(v, 0)
        if r > rank:
            rank = r
            verdict = v
    return verdict, reasons


def local_remainder_verdict(case: dict[str, Any]) -> tuple[str, list[str], dict[str, Any]]:
    """Fail-closed remainder analysis. CERTIFIED only with no defects."""
    defects: list[tuple[str, str]] = []
    family = str(case.get("function_family") or "")
    order = _as_int(case.get("function_order"))
    N = _as_int(case.get("expansion_order"))
    prefactor = int(case.get("prefactor_power") or 0)
    needed = int(case.get("needed_vanish_power") if case.get("needed_vanish_power") is not None else 1)
    t_sym = _t_symbol(case)
    z0 = _parse(case.get("expansion_point"), case)
    arg = _parse(case.get("argument"), case)
    affine = _affine_coeffs(arg, t_sym) if arg is not None else None
    z0_aff, slope = affine if affine is not None else (z0, None)
    z0_use = z0_aff if z0_aff is not None else z0
    pole_kind = _classify_z0(z0_use, family, order, case, t_sym)
    dist = _distance_value(z0_use, family, order)
    vanish = None if N is None else N + 1 + prefactor

    if not case.get("domain_conditions"):
        defects.append((UNKNOWN, "empty_domain"))
    if is_class_c_or_d(case):
        defects.append((ASSUMPTION_REQUIRED, "class_c_or_d"))
    if pole_kind == "pole":
        defects.append((NONANALYTIC, "expansion_point_pole"))
    elif pole_kind == "unknown":
        defects.append((ASSUMPTION_REQUIRED, "z0_may_be_pole"))
    if _denominator_vanishes(case, t_sym):
        defects.append((NONANALYTIC, "hidden_denominator_zero"))
    if _arbitrarily_close_pole(z0_use, slope, family, order) and pole_kind != "pole":
        defects.append((UNKNOWN, "path_cross_pole"))
    if N is None:
        defects.append((UNKNOWN, "missing_order"))
    elif vanish is not None and vanish < needed:
        if prefactor < 0 and vanish <= 0:
            defects.append((UNKNOWN, "divergent_prefactor"))
        else:
            defects.append((UNKNOWN, "insufficient_order"))
    if _complex_perturbation(case) and _real_only_assumption(case):
        defects.append((ASSUMPTION_REQUIRED, "real_only_on_complex"))
    if _bound_contains_singularity(case, dist):
        defects.append((UNKNOWN, "bound_contains_pole"))
    if _symbolic_M_unproved(case):
        defects.append((ASSUMPTION_REQUIRED, "M_unproved"))
    if case.get("force_remainder_unknown"):
        defects.append((UNKNOWN, "remainder_slot_unknown"))

    verdict, reasons = _combine(defects)
    info = {
        "pole_kind": pole_kind,
        "vanish_power": vanish,
        "needed_vanish_power": needed,
        "prefactor_power": prefactor,
        "expansion_order": N,
        "distance": None if dist is None else str(dist),
        "slope": None if slope is None else str(slope),
        "z0": None if z0_use is None else str(z0_use),
        "reasons": reasons,
    }
    return verdict, reasons, info


def _neighborhood_for(verdict: str) -> str:
    if verdict == CERTIFIED:
        return NEIGHBORHOOD_CERTIFIED
    if verdict == ASSUMPTION_REQUIRED:
        return NEIGHBORHOOD_ASSUMPTION
    return NEIGHBORHOOD_UNKNOWN


def _call_compile_remainder(
    fn: Any,
    case: dict[str, Any],
    claimed: RemainderCertificate,
) -> tuple[Any, str | None]:
    attempts: list[tuple[tuple[Any, ...], dict[str, Any]]] = [
        ((case,), {}),
        ((claimed,), {}),
        ((), {"case": case}),
        ((), {"cert": claimed}),
        ((), {"certificate": claimed}),
    ]
    try:
        sig = inspect.signature(fn)
        names = list(sig.parameters)
    except Exception:
        names = []
    if names and names[0] in {"cert", "certificate"}:
        attempts.insert(0, ((claimed,), {}))
    elif names and names[0] in {"case", "payload", "attack"}:
        attempts.insert(0, ((case,), {}))
    last_err = None
    for args, kwargs in attempts:
        try:
            return fn(*args, **kwargs), None
        except TypeError as exc:
            last_err = f"TypeError: {exc}"[:240]
            continue
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"[:300]
    return None, last_err or "no_matching_signature"


def _compiler_verdict(out: Any, case: dict[str, Any]) -> str | None:
    if out is None:
        return None
    if isinstance(out, RemainderCertificate):
        return validate_certificate(out)
    if isinstance(out, str):
        if out not in REMAINDER_VERDICTS:
            return UNKNOWN
        if out != CERTIFIED:
            return out
        claimed = claimed_certificate(case)
        claimed.verdict = CERTIFIED
        return validate_certificate(claimed)
    inner = None
    verdict_s = None
    if isinstance(out, dict):
        inner = out.get("certificate") or out.get("cert")
        verdict_s = out.get("verdict") or out.get("remainder_verdict")
    elif hasattr(out, "verdict"):
        inner = out
        verdict_s = getattr(out, "verdict", None)
    if isinstance(inner, RemainderCertificate):
        return validate_certificate(inner)
    if isinstance(inner, dict):
        allowed = {f.name for f in fields(RemainderCertificate)}
        try:
            cert = RemainderCertificate(
                **{k: v for k, v in inner.items() if k in allowed}
            )
            return validate_certificate(cert)
        except Exception:
            pass
    if verdict_s:
        if verdict_s not in REMAINDER_VERDICTS:
            return UNKNOWN
        if verdict_s != CERTIFIED:
            return str(verdict_s)
        claimed = claimed_certificate(case)
        claimed.verdict = CERTIFIED
        return validate_certificate(claimed)
    return None


def sound_certificate(
    case: dict[str, Any],
    verdict: str,
    reasons: list[str],
) -> RemainderCertificate:
    cert = claimed_certificate(case)
    cert.verdict = verdict
    cert.neighborhood_verdict = _neighborhood_for(verdict)
    cert.note = ",".join(reasons) if reasons else str(case.get("trap") or "")
    cert.method_version = METHOD_VERSION
    return cert


def check_case(case: dict[str, Any]) -> CaseResult:
    claimed = claimed_certificate(case)
    schema_verdict = validate_certificate(claimed)
    local_v, reasons, info = local_remainder_verdict(case)
    class_c = is_class_c_or_d(case)
    should = bool(case.get("should_be_certified"))
    should_hop_zero = bool(case.get("should_be_hop_zero"))

    compiler_v = None
    compiler_note = None
    fn = discover_compile_remainder()
    if fn is not None:
        raw, compiler_note = _call_compile_remainder(fn, case, claimed)
        compiler_v = _compiler_verdict(raw, case)

    hop_v = None
    hop_lvl = None
    trap = None
    hop = case.get("hop")
    if hop:
        hop_v, hop_lvl = compose_hop_verdict(
            reconstruction_ok=bool(hop.get("reconstruction_ok")),
            atoms_expanded=bool(hop.get("atoms_expanded")),
            negative_verdict=str(hop.get("negative_verdict")),
            constant_verdict=str(hop.get("constant_verdict")),
            remainder_verdict=str(hop.get("remainder_verdict")),
        )
        trap = forbidden_ignore_remainder(
            negative_verdict=str(hop.get("negative_verdict")),
            constant_verdict=str(hop.get("constant_verdict")),
            remainder_verdict=str(hop.get("remainder_verdict")),
        )

    got = local_v
    false_certified = bool(
        (got == CERTIFIED and not should)
        or (class_c and schema_verdict == CERTIFIED)
        or (compiler_v == CERTIFIED and not should)
        or (hop_v == HOP_ZERO and not should_hop_zero)
    )
    cert = sound_certificate(case, got, reasons)
    extra = dict(case.get("extra") or {})
    extra.update(info)
    extra.update(
        {
            "trap": case.get("trap"),
            "schema_verdict": schema_verdict,
            "compiler_verdict": compiler_v,
            "compiler_note": compiler_note,
            "hop_verdict": hop_v,
            "hop_level": hop_lvl,
            "class_c": class_c,
            "claimed_verdict": case.get("claimed_verdict"),
        }
    )
    return CaseResult(
        case_id=str(case["id"]),
        kind=str(case.get("kind") or ""),
        expect=str(case.get("expect") or UNKNOWN),
        got=got,
        false_certified=false_certified,
        schema_verdict=schema_verdict,
        local_verdict=local_v,
        compiler_verdict=compiler_v,
        hop_verdict=hop_v,
        hop_level=hop_lvl,
        trap_ignore_remainder=trap,
        class_c=class_c,
        extra=extra,
        certificate=cert,
    )


def check_all(
    cases: Optional[list[dict[str, Any]]] = None,
) -> list[CaseResult]:
    if cases is None:
        cases = ATTACK_CASES
    return [check_case(c) for c in cases]


def check_controls() -> list[CaseResult]:
    return [check_case(c) for c in CONTROL_CASES]


def false_certified_count(results: Optional[list[CaseResult]] = None) -> int:
    if results is None:
        results = check_all()
    return sum(1 for r in results if r.false_certified or (r.got == CERTIFIED and r.expect != CERTIFIED))


def run_cases() -> dict[str, Any]:
    results = [check_case(c) for c in load_all_cases()]
    n_false = sum(
        1
        for r in results
        if r.false_certified or (r.got == CERTIFIED and r.expect != CERTIFIED)
    )
    return {
        "n": len(results),
        "n_false_certified": n_false,
        "rows": [r.row() for r in results],
    }



