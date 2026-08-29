"""Compile atom-local remainder certificates.

Inputs: function atom + affine argument + domain certificate + Taylor
order. Sibling packages (affine, neighborhood, cauchy, polygamma,
analysis) are optional; missing imports fail closed as UNKNOWN and
never fake CERTIFIED. Optional callables inject those steps.

CERTIFIED remainder is not hop ZERO. No hop composer. D2 LOCKED.
"""
from __future__ import annotations

import importlib
from typing import Any, Callable, Optional, Sequence

from research.remainder_certification.compiler.builders import (
    EMPTY_DOMAIN_CONDITION,
    affine_fields,
    as_nonneg_int,
    as_step_dict,
    atom_fields,
    domain_fields,
    finalize_certificate,
    merge_assumptions,
    merge_domain_verdicts,
    merge_texts,
    neighborhood_is_certified,
    pick,
    remainder_form_for_order,
    uses_blocking_assumptions,
)
from research.remainder_certification.schema import (
    ASSUMPTION_REQUIRED,
    CERTIFIED,
    METHOD_VERSION,
    NEIGHBORHOOD_ASSUMPTION,
    NEIGHBORHOOD_CERTIFIED,
    NEIGHBORHOOD_UNKNOWN,
    NONANALYTIC,
    RemainderCertificate,
    UNKNOWN,
    UNSUPPORTED,
)

StepFn = Callable[[dict[str, Any]], Any]

SIBLING_PACKAGES = {
    "affine": "research.remainder_certification.affine",
    "neighborhood": "research.remainder_certification.neighborhood",
    "cauchy": "research.remainder_certification.cauchy",
    "polygamma": "research.remainder_certification.polygamma",
    "analysis": "research.remainder_certification.analysis",
}

_ENTRYPOINTS = {
    "affine": ("compile_step", "normalize_affine", "normalize"),
    "neighborhood": ("compile_step", "certify_neighborhood", "certify"),
    "cauchy": ("compile_step", "cauchy_bound", "bound"),
    "polygamma": (
        "compile_step",
        "polygamma_domain",
        "certify_domain",
        "certify",
    ),
    "analysis": ("compile_step", "certify_analyticity", "certify"),
}

_PG_MARKERS = ("polygamma", "digamma", "trigamma", "loggamma", "psi")


def resolve_step(
    name: str, injected: Optional[StepFn]
) -> tuple[Optional[StepFn], str]:
    """Return (callable, source). Missing package/entrypoint is fail-closed."""
    if injected is not None:
        if not callable(injected):
            return None, "injected_not_callable"
        return injected, "injected"
    mod_name = SIBLING_PACKAGES.get(name)
    if not mod_name:
        return None, "unknown_step"
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None, "missing_package"
    for attr in _ENTRYPOINTS.get(name, ("compile_step",)):
        fn = getattr(mod, attr, None)
        if callable(fn):
            return fn, f"package:{attr}"
    return None, "missing_entrypoint"


def sibling_status() -> dict[str, str]:
    return {name: resolve_step(name, None)[1] for name in SIBLING_PACKAGES}


def compile_remainder(
    atom: Any,
    affine_argument: Any = None,
    domain_certificate: Any = None,
    taylor_order: Any = None,
    *,
    affine: Optional[StepFn] = None,
    neighborhood: Optional[StepFn] = None,
    cauchy: Optional[StepFn] = None,
    polygamma: Optional[StepFn] = None,
    analysis: Optional[StepFn] = None,
    declared_assumptions: Optional[Sequence[Any]] = None,
) -> RemainderCertificate:
    """Compile one atom remainder. Never a hop certificate."""
    family_info = atom_fields(atom)
    function_family = family_info["function_family"]
    function_order = family_info["function_order"]
    order_n = as_nonneg_int(taylor_order)
    taylor_ok = order_n is not None

    affine_in = affine_fields(affine_argument)
    extra = _affine_from_atom(atom)
    if extra is not None:
        for key in ("expansion_point", "perturbation", "argument"):
            if extra[key] and not affine_in[key]:
                affine_in[key] = extra[key]
        if extra["structured"]:
            affine_in["structured"] = True
            affine_in["ok"] = True
    if not affine_in["argument"] and family_info["argument"]:
        affine_in["argument"] = family_info["argument"]

    domain_in_present = domain_certificate not in (None, "")
    domain_in = (
        domain_fields(domain_certificate)
        if domain_in_present
        else domain_fields({})
    )
    if domain_in["function_family"] and not function_family:
        function_family = domain_in["function_family"]
    if domain_in["function_order"] and not function_order:
        function_order = domain_in["function_order"]

    declared = merge_assumptions(declared_assumptions)

    affine_fn, affine_src = resolve_step("affine", affine)
    neigh_fn, neigh_src = resolve_step("neighborhood", neighborhood)
    cauchy_fn, cauchy_src = resolve_step("cauchy", cauchy)
    pg_fn, pg_src = resolve_step("polygamma", polygamma)
    analysis_fn, analysis_src = resolve_step("analysis", analysis)

    payload = _payload(
        atom=atom,
        affine_argument=affine_argument,
        domain_certificate=domain_certificate,
        taylor_order=order_n,
        function_family=function_family,
        function_order=function_order,
        expansion_point=affine_in["expansion_point"],
        perturbation=affine_in["perturbation"],
        argument=affine_in["argument"],
        declared_assumptions=declared,
    )

    affine_res, affine_present = _run(affine_fn, payload)
    affine_out = affine_fields(affine_res) if affine_present else affine_in
    if affine_present:
        if not affine_out["argument"] and affine_in["argument"]:
            affine_out["argument"] = affine_in["argument"]
        if not affine_out["expansion_point"] and affine_in["expansion_point"]:
            affine_out["expansion_point"] = affine_in["expansion_point"]
        if not affine_out["perturbation"] and affine_in["perturbation"]:
            affine_out["perturbation"] = affine_in["perturbation"]
    elif affine_in["structured"]:
        affine_out = affine_in
        affine_out["ok"] = True
    else:
        affine_out = affine_in
        affine_out["ok"] = False

    if affine_out.get("unsupported"):
        affine_out["ok"] = False

    payload["expansion_point"] = affine_out["expansion_point"]
    payload["perturbation"] = affine_out["perturbation"]
    payload["argument"] = affine_out["argument"] or payload["argument"]

    analysis_res, analysis_present = _run(analysis_fn, payload)
    pg_res, pg_present = _run(pg_fn, payload)

    domain_verdict, domain_merged = _merge_domain(
        domain_in_present=domain_in_present,
        domain_in=domain_in,
        analysis_present=analysis_present,
        analysis_res=analysis_res,
        pg_present=pg_present,
        pg_res=pg_res,
        function_family=function_family,
    )

    neigh_res, neigh_present = _run(neigh_fn, payload)
    neigh_verdict = NEIGHBORHOOD_UNKNOWN
    if neigh_present:
        neigh_verdict = str(pick(neigh_res, "verdict", "neighborhood_verdict") or UNKNOWN)
        if neigh_verdict == CERTIFIED:
            neigh_verdict = NEIGHBORHOOD_UNKNOWN
        if neigh_verdict == UNSUPPORTED:
            neigh_verdict = NEIGHBORHOOD_UNKNOWN
        if neigh_verdict not in (
            NEIGHBORHOOD_CERTIFIED,
            NEIGHBORHOOD_ASSUMPTION,
            NEIGHBORHOOD_UNKNOWN,
        ):
            if neigh_verdict == ASSUMPTION_REQUIRED:
                neigh_verdict = NEIGHBORHOOD_ASSUMPTION
            else:
                neigh_verdict = NEIGHBORHOOD_UNKNOWN

    cauchy_res, cauchy_present = _run(cauchy_fn, payload)
    cauchy_ok = _cauchy_ok(cauchy_res) if cauchy_present else False

    assumptions = merge_assumptions(
        declared,
        domain_merged.get("assumptions_used"),
        affine_out.get("assumptions_used"),
        analysis_res.get("assumptions_used") if analysis_present else None,
        pg_res.get("assumptions_used") if pg_present else None,
        neigh_res.get("assumptions_used") if neigh_present else None,
        cauchy_res.get("assumptions_used") if cauchy_present else None,
    )
    conditions = merge_texts(
        domain_merged.get("domain_conditions"),
        affine_out.get("domain_conditions"),
        analysis_res.get("domain_conditions") if analysis_present else None,
        analysis_res.get("conditions") if analysis_present else None,
        pg_res.get("domain_conditions") if pg_present else None,
        pg_res.get("conditions") if pg_present else None,
        neigh_res.get("domain_conditions") if neigh_present else None,
        neigh_res.get("conditions") if neigh_present else None,
        cauchy_res.get("domain_conditions") if cauchy_present else None,
    )
    deps = merge_texts(
        domain_merged.get("proof_dependencies"),
        affine_out.get("proof_dependencies"),
        analysis_res.get("proof_dependencies") if analysis_present else None,
        pg_res.get("proof_dependencies") if pg_present else None,
        neigh_res.get("proof_dependencies") if neigh_present else None,
        cauchy_res.get("proof_dependencies") if cauchy_present else None,
    )

    affine_ok = bool(affine_out.get("ok")) and not bool(affine_out.get("unsupported"))
    blocking = uses_blocking_assumptions(assumptions)
    verdict = _compose_verdict(
        taylor_ok=taylor_ok,
        affine_ok=affine_ok,
        domain_verdict=domain_verdict,
        neighborhood_verdict=neigh_verdict,
        neighborhood_present=neigh_present,
        cauchy_ok=cauchy_ok,
        cauchy_present=cauchy_present,
        blocking=blocking,
    )

    remainder_form = str(pick(cauchy_res, "remainder_form", "form") or "")
    if not remainder_form and order_n is not None:
        remainder_form = remainder_form_for_order(order_n)
    bound = str(pick(cauchy_res, "bound") or "")
    distance = str(
        pick(neigh_res, "distance_to_singularity", "distance")
        or domain_merged.get("distance_to_singularity")
        or ""
    )
    small_t = str(
        pick(neigh_res, "required_small_t_condition", "small_t")
        or domain_merged.get("required_small_t_condition")
        or ""
    )
    analyticity = domain_merged.get("analyticity_certificate") or {}
    if not analyticity:
        if analysis_present:
            analyticity = {
                "status": "unproved",
                "reason": "analysis step returned no certificate",
            }
        else:
            analyticity = {
                "status": "unproved",
                "reason": "analysis sibling not available",
            }

    missing = [
        name
        for name, src in (
            ("affine", affine_src),
            ("neighborhood", neigh_src),
            ("cauchy", cauchy_src),
            ("polygamma", pg_src),
            ("analysis", analysis_src),
        )
        if src.startswith("missing")
    ]
    notes = [
        "atom-local remainder certificate; not a hop certificate",
        "CERTIFIED remainder is not hop ZERO",
        f"method_version={METHOD_VERSION}",
    ]
    if missing:
        notes.append("missing_siblings:" + ",".join(missing))
    for src_name, src in (
        ("affine", affine_src),
        ("neighborhood", neigh_src),
        ("cauchy", cauchy_src),
        ("polygamma", pg_src),
        ("analysis", analysis_src),
    ):
        notes.append(f"{src_name}:{src}")
    if affine_out.get("note"):
        notes.append(str(affine_out["note"]))
    for res in (analysis_res, pg_res, neigh_res, cauchy_res):
        extra = res.get("note")
        if extra:
            notes.append(str(extra))
    if not conditions:
        conditions = [EMPTY_DOMAIN_CONDITION]
        if verdict == CERTIFIED:
            verdict = UNKNOWN

    argument = str(affine_out.get("argument") or payload.get("argument") or "")
    cert = RemainderCertificate(
        function_family=function_family,
        function_order=str(function_order or ""),
        argument=argument,
        expansion_point=str(affine_out.get("expansion_point") or ""),
        perturbation=str(affine_out.get("perturbation") or ""),
        expansion_order=order_n,
        domain_conditions=conditions,
        analyticity_certificate=analyticity,
        distance_to_singularity=distance,
        remainder_form=remainder_form,
        bound=bound,
        required_small_t_condition=small_t,
        assumptions_used=assumptions,
        proof_dependencies=deps,
        verdict=verdict,
        neighborhood_verdict=neigh_verdict,
        method_version=METHOD_VERSION,
        note="; ".join(notes),
    )
    return finalize_certificate(cert)


def _affine_from_atom(atom: Any) -> Optional[dict[str, Any]]:
    if atom is None or isinstance(atom, str):
        return None
    keys = (
        "expansion_point",
        "perturbation",
        "argument",
        "z0",
        "alpha_0",
        "c",
    )
    if isinstance(atom, dict):
        if any(key in atom for key in keys):
            return affine_fields(atom)
        return None
    if any(hasattr(atom, key) for key in keys):
        return affine_fields(atom)
    return None


def _payload(**fields: Any) -> dict[str, Any]:
    return dict(fields)


def _run(fn: Optional[StepFn], payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if fn is None:
        return {}, False
    try:
        raw = fn(dict(payload))
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__, "verdict": UNKNOWN}, True
    data = as_step_dict(raw)
    if "ok" not in data and "verdict" not in data and not data:
        data = {"ok": False, "verdict": UNKNOWN}
    return data, True


def _cauchy_ok(result: dict[str, Any]) -> bool:
    if result.get("ok") is True:
        return True
    if result.get("ok") is False:
        return False
    return str(result.get("verdict") or "") == CERTIFIED


def _is_polygamma_family(family: str) -> bool:
    text = (family or "").lower()
    return any(marker in text for marker in _PG_MARKERS)


def _merge_domain(
    *,
    domain_in_present: bool,
    domain_in: dict[str, Any],
    analysis_present: bool,
    analysis_res: dict[str, Any],
    pg_present: bool,
    pg_res: dict[str, Any],
    function_family: str,
) -> tuple[str, dict[str, Any]]:
    analysis_dom = domain_fields(analysis_res) if analysis_present else domain_fields({})
    pg_dom = domain_fields(pg_res) if pg_present else domain_fields({})
    verdicts: list[str] = []
    if domain_in_present:
        verdicts.append(str(domain_in.get("verdict") or UNKNOWN))
    if analysis_present:
        verdicts.append(str(analysis_dom.get("verdict") or UNKNOWN))
    pg_counts = False
    if pg_present:
        pg_v = str(pg_dom.get("verdict") or UNKNOWN)
        pg_counts = _is_polygamma_family(function_family) or pg_v in (
            NONANALYTIC,
            ASSUMPTION_REQUIRED,
            CERTIFIED,
        )
        if pg_counts:
            verdicts.append(pg_v)
    merged = {
        "verdict": merge_domain_verdicts(verdicts),
        "domain_conditions": merge_texts(
            domain_in.get("domain_conditions") if domain_in_present else None,
            analysis_dom.get("domain_conditions") if analysis_present else None,
            pg_dom.get("domain_conditions") if pg_counts else None,
        ),
        "analyticity_certificate": dict(
            (pg_dom.get("analyticity_certificate") if pg_counts else None)
            or (analysis_dom.get("analyticity_certificate") if analysis_present else None)
            or (domain_in.get("analyticity_certificate") if domain_in_present else None)
            or {}
        ),
        "distance_to_singularity": str(
            (pg_dom.get("distance_to_singularity") if pg_counts else "")
            or (analysis_dom.get("distance_to_singularity") if analysis_present else "")
            or (domain_in.get("distance_to_singularity") if domain_in_present else "")
            or ""
        ),
        "assumptions_used": merge_assumptions(
            domain_in.get("assumptions_used") if domain_in_present else None,
            analysis_dom.get("assumptions_used") if analysis_present else None,
            pg_dom.get("assumptions_used") if pg_counts else None,
        ),
        "proof_dependencies": merge_texts(
            domain_in.get("proof_dependencies") if domain_in_present else None,
            analysis_dom.get("proof_dependencies") if analysis_present else None,
            pg_dom.get("proof_dependencies") if pg_counts else None,
        ),
        "required_small_t_condition": str(
            (pg_dom.get("required_small_t_condition") if pg_counts else "")
            or (
                analysis_dom.get("required_small_t_condition")
                if analysis_present
                else ""
            )
            or (
                domain_in.get("required_small_t_condition")
                if domain_in_present
                else ""
            )
            or ""
        ),
    }
    return str(merged["verdict"]), merged


def _compose_verdict(
    *,
    taylor_ok: bool,
    affine_ok: bool,
    domain_verdict: str,
    neighborhood_verdict: str,
    neighborhood_present: bool,
    cauchy_ok: bool,
    cauchy_present: bool,
    blocking: bool,
) -> str:
    if domain_verdict == NONANALYTIC:
        return NONANALYTIC
    if not taylor_ok or not affine_ok:
        return UNKNOWN
    steps_ready = neighborhood_present and cauchy_present
    can_certify = (
        domain_verdict == CERTIFIED
        and neighborhood_is_certified(neighborhood_verdict)
        and cauchy_ok
        and steps_ready
        and not blocking
    )
    if can_certify:
        return CERTIFIED
    would_certify = (
        domain_verdict == CERTIFIED
        and neighborhood_is_certified(neighborhood_verdict)
        and cauchy_ok
        and steps_ready
    )
    if would_certify and blocking:
        return ASSUMPTION_REQUIRED
    if (
        domain_verdict == ASSUMPTION_REQUIRED
        or neighborhood_verdict == NEIGHBORHOOD_ASSUMPTION
    ):
        return ASSUMPTION_REQUIRED
    return UNKNOWN
