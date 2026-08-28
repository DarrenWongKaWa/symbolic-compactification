"""Attack hop ZERO. Do not improve schema or sibling V5 packages.

Per-atom series fill reconstruction / negative / t^0 / remainder
verdicts. ``schema.compose_hop_verdict`` is the only hop rule.
t^0 match, LEVEL A atom-series, and vanished poles without remainder
are recorded as traps, never as certificates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import sympy

from research.coefficient_laurent.schema import (
    LaurentAtom,
    LaurentCertificate,
    LaurentCoefficientRecord,
    METHOD_VERSION,
    compose_hop_verdict,
)
from research.coefficient_laurent.falsifier.cases import (
    ATTACK_CASES,
    CONTROL_CASES,
    load_all_cases,
)
from research.coefficient_laurent.falsifier.expr import (
    NONZERO,
    UNKNOWN,
    ZERO,
    laurent_coeffs,
    parse_text,
    series_atom,
    symbol_map,
    unevaluated_sum,
    verdict_with_probes,
)


@dataclass
class CaseResult:
    case_id: str
    kind: str
    expect: str
    got: str
    proof_level: str
    false_zero: bool
    reconstruction_ok: bool
    atoms_expanded: bool
    negative_verdict: str
    constant_verdict: str
    remainder_verdict: str
    trap_t0: str
    trap_level_a: str
    trap_ignore_remainder: str
    extra: dict[str, Any] = field(default_factory=dict)
    certificate: Optional[LaurentCertificate] = None

    def row(self) -> dict[str, str]:
        return {"id": self.case_id, "expect": self.expect, "got": self.got}

    @property
    def compose_kwargs(self) -> dict[str, Any]:
        return {
            "reconstruction_ok": self.reconstruction_ok,
            "atoms_expanded": self.atoms_expanded,
            "negative_verdict": self.negative_verdict,
            "constant_verdict": self.constant_verdict,
            "remainder_verdict": self.remainder_verdict,
        }


def forbidden_t0_is_zero(constant_verdict: str) -> str:
    """Forbidden composer: t^0 match => hop ZERO even if a pole survives."""
    if constant_verdict == ZERO:
        return ZERO
    if constant_verdict == NONZERO:
        return NONZERO
    return UNKNOWN


def forbidden_level_a_is_zero(*, reconstruction_ok: bool, atoms_expanded: bool) -> str:
    """Forbidden composer: atom series success is hop ZERO."""
    if atoms_expanded and reconstruction_ok:
        return ZERO
    if atoms_expanded:
        return ZERO
    return UNKNOWN


def forbidden_ignore_remainder(
    *,
    negative_verdict: str,
    constant_verdict: str,
) -> str:
    """Forbidden composer: vanished poles (and optional t^0) skip remainder."""
    if negative_verdict == NONZERO or constant_verdict == NONZERO:
        return NONZERO
    if negative_verdict == ZERO:
        return ZERO
    return UNKNOWN


def _atom_text(raw: Any) -> str:
    if isinstance(raw, dict):
        return str(raw.get("text") or "")
    return str(raw or "")


def _parse_hop(
    case: dict[str, Any],
) -> tuple[list[Any], Any, Any, dict[str, Any]]:
    symbols = list(case.get("symbols") or [])
    atom_texts = [_atom_text(a) for a in (case.get("atoms") or [])]
    atoms = [parse_text(text, symbols) for text in atom_texts]
    source_atom_texts = case.get("source_atoms")
    if source_atom_texts:
        source_parts = [parse_text(text, symbols) for text in source_atom_texts]
        source = unevaluated_sum(source_parts)
    elif case.get("source"):
        source = parse_text(case.get("source"), symbols)
    else:
        source = unevaluated_sum(atoms)
    target = parse_text(case.get("target"), symbols)
    smap = symbol_map(
        *[e for e in atoms + [source, target] if e is not None]
    )
    for spec in symbols:
        name = spec["name"] if isinstance(spec, dict) else str(spec)
        real = True if not isinstance(spec, dict) else spec.get("real", True)
        if name not in smap:
            smap[name] = sympy.Symbol(name, real=bool(real))
    return atoms, source, target, smap


def _certified_power(k: int, order_n: Optional[int]) -> bool:
    if order_n is None:
        return True
    return k < order_n


def _merge_verdict(current: str, incoming: str) -> str:
    if incoming == NONZERO or current == NONZERO:
        return NONZERO
    if incoming == UNKNOWN or current == UNKNOWN:
        return UNKNOWN
    return ZERO


def check_case(case: dict[str, Any]) -> CaseResult:
    atoms, source, target, smap = _parse_hop(case)
    probes = list(case.get("probes") or [])
    nterms = int(case.get("series_nterms") if case.get("series_nterms") is not None else 4)
    nmin = int(case.get("required_power_min") if case.get("required_power_min") is not None else -6)
    nmax = int(case.get("required_power_max") if case.get("required_power_max") is not None else 0)
    var_name = str(case.get("degeneration_variable") or "t")
    var = smap.get(var_name)

    recon_v, recon_res = verdict_with_probes(
        unevaluated_sum(atoms) if atoms else None,
        source,
        probes,
        smap,
    )
    reconstruction_ok = recon_v == ZERO

    series_rows: list[dict[str, Any]] = []
    combined: Any = sympy.Integer(0)
    atoms_expanded = True
    order_n: Optional[int] = None
    atom_records: list[dict[str, Any]] = []
    atom_ir: list[dict[str, Any]] = []
    if not atoms or var is None:
        atoms_expanded = False
    for i, atom in enumerate(atoms):
        text = _atom_text((case.get("atoms") or [])[i] if i < len(case.get("atoms") or []) else "")
        cls = "POLYGAMMA" if "polygamma" in text else "RATIONAL"
        atom_ir.append(
            LaurentAtom(
                atom_id=f"a{i}",
                source_member=str(case["id"]),
                argument=text,
                degeneration_variable=var_name,
                target_value=str(case.get("target_value") or "0"),
                function_head="polygamma" if cls == "POLYGAMMA" else "",
                atom_class=cls,
            ).to_dict()
        )
        s, atom_order, note = series_atom(atom, var, nterms)
        series_rows.append(
            {
                "index": i,
                "note": note,
                "order_n": atom_order,
                "series": None if s is None else str(s)[:300],
            }
        )
        if s is None:
            atoms_expanded = False
            continue
        combined = combined + s
        if atom_order is not None:
            order_n = atom_order if order_n is None else min(order_n, atom_order)
        finite_i = s.removeO() if isinstance(s, sympy.Expr) and s.has(sympy.Order) else s
        per = laurent_coeffs(finite_i, var, nmin=nmin, nmax=nmax) if var is not None else None
        if per is None:
            continue
        for power, ck in per.items():
            atom_records.append(
                LaurentCoefficientRecord(
                    atom_id=f"a{i}",
                    power=int(power),
                    coefficient_expr=str(ck),
                    exact=_certified_power(int(power), atom_order),
                    method="per_atom_series",
                    provenance=["atom_series", f"nterms:{nterms}"],
                ).to_dict()
            )

    if combined.has(sympy.Order) if isinstance(combined, sympy.Expr) else False:
        o = combined.getO() if hasattr(combined, "getO") else None
        if o is not None:
            try:
                order_n = int(o.getn())
            except Exception:
                order_n = 0 if order_n is None else order_n
        finite = combined.removeO()
    else:
        finite = combined
        if atoms_expanded and all(row["order_n"] is None for row in series_rows):
            order_n = None

    coeffs = laurent_coeffs(finite, var, nmin=nmin, nmax=nmax) if atoms_expanded else None
    coeff_rows: list[dict[str, Any]] = []
    negative_verdict = UNKNOWN if not atoms_expanded or coeffs is None else ZERO
    if coeffs is not None:
        for k in range(nmin, 0):
            ck = coeffs.get(k, sympy.Integer(0))
            if not _certified_power(k, order_n):
                slot = UNKNOWN
                negative_verdict = _merge_verdict(negative_verdict, UNKNOWN)
            else:
                slot, _ = verdict_with_probes(ck, sympy.Integer(0), probes, smap)
                negative_verdict = _merge_verdict(negative_verdict, slot)
            coeff_rows.append({"power": k, "coeff": str(ck)[:200], "verdict": slot})

    if not atoms_expanded or coeffs is None:
        constant_verdict = UNKNOWN
        c0 = None
    elif not _certified_power(0, order_n):
        constant_verdict = UNKNOWN
        c0 = None
        coeff_rows.append({"power": 0, "coeff": None, "verdict": UNKNOWN})
    else:
        c0 = coeffs.get(0, sympy.Integer(0))
        constant_verdict, _ = verdict_with_probes(c0, target, probes, smap)
        coeff_rows.append(
            {
                "power": 0,
                "coeff": str(c0)[:200],
                "verdict": constant_verdict,
            }
        )

    if not atoms_expanded:
        remainder_verdict = UNKNOWN
    elif order_n is None or order_n > 0:
        remainder_verdict = ZERO
    else:
        remainder_verdict = UNKNOWN

    got, proof_level = compose_hop_verdict(
        reconstruction_ok=reconstruction_ok,
        atoms_expanded=atoms_expanded,
        negative_verdict=negative_verdict,
        constant_verdict=constant_verdict,
        remainder_verdict=remainder_verdict,
    )
    expect = str(case.get("expect") or UNKNOWN)
    should = bool(case.get("should_be_zero") is True)
    false_zero = got == ZERO and not should

    trap_t0 = forbidden_t0_is_zero(constant_verdict)
    trap_level_a = forbidden_level_a_is_zero(
        reconstruction_ok=reconstruction_ok,
        atoms_expanded=atoms_expanded,
    )
    trap_ignore_remainder = forbidden_ignore_remainder(
        negative_verdict=negative_verdict,
        constant_verdict=constant_verdict,
    )

    summed = {str(k): str(v) for k, v in (coeffs or {}).items()}
    cert = LaurentCertificate(
        source_member=str(case["id"]),
        target_member="target",
        degeneration_variable=var_name,
        target_value=str(case.get("target_value") or "0"),
        required_power_min=nmin,
        required_power_max=nmax,
        atom_records=atom_records,
        summed_coefficients=summed,
        negative_coefficients_verdict=negative_verdict,
        constant_term_verdict=constant_verdict,
        remainder_verdict=remainder_verdict,
        final_verdict=got,
        proof_level=proof_level,
        method_version=METHOD_VERSION,
        max_intermediate_ops=None,
        used_full_together=False,
    )

    extra = dict(case.get("extra") or {})
    extra.update(
        {
            "trap": case.get("trap"),
            "nterms": nterms,
            "order_n": order_n,
            "reconstruction_verdict": recon_v,
            "reconstruction_residual": None if recon_res is None else str(recon_res)[:200],
            "series": series_rows,
            "coefficients": coeff_rows,
            "c0": None if c0 is None else str(c0)[:200],
            "finite": None if finite is None else str(finite)[:200],
            "atoms": [str(a)[:200] if a is not None else None for a in atoms],
            "atom_ir": atom_ir,
        }
    )
    return CaseResult(
        case_id=str(case["id"]),
        kind=str(case.get("kind") or ""),
        expect=expect,
        got=got,
        proof_level=proof_level,
        false_zero=false_zero,
        reconstruction_ok=reconstruction_ok,
        atoms_expanded=atoms_expanded,
        negative_verdict=negative_verdict,
        constant_verdict=constant_verdict,
        remainder_verdict=remainder_verdict,
        trap_t0=trap_t0,
        trap_level_a=trap_level_a,
        trap_ignore_remainder=trap_ignore_remainder,
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


def false_zero_count(results: Optional[list[CaseResult]] = None) -> int:
    if results is None:
        results = check_all(load_all_cases())
    return sum(1 for r in results if r.false_zero or (r.got == ZERO and r.expect != ZERO))


def run_cases() -> dict[str, Any]:
    results = [check_case(c) for c in load_all_cases()]
    n_false = sum(1 for r in results if r.got == ZERO and r.expect != ZERO)
    return {
        "n": len(results),
        "n_false_zero": n_false,
        "rows": [r.row() for r in results],
    }
