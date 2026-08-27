"""Guo G1–G4 on frozen raw outputs. Not a compact-form score."""
from __future__ import annotations

from typing import Any

from research.llm_abstraction.schema import LLMStructureHypothesis, OK
from research.obligation_ir.schema import COMPILE_OK, DIVIDED_DIFFERENCE, CONFLUENCE

G1_TYPES = frozenset({
    "divided_difference", "confluent_representation",
    "derivative_family", "master_function", "symmetry_invariant",
    "tensor_generator",
})

_EXPLICIT = (
    "divided difference", "divided_difference", "confluent",
    "F[", "F_+", "F_-", "node", "polygamma", "loggamma", "log_gamma",
)


def g1_discovery(hyps: list[LLMStructureHypothesis]) -> dict[str, Any]:
    """Explicit representation class, not 'maybe unified'."""
    hits = []
    for h in hyps:
        if h.parse_status != OK:
            continue
        if h.hypothesis_type not in G1_TYPES:
            continue
        blob = " ".join([
            h.hypothesis_type, h.latent_object or "", h.rationale or "",
            " ".join(h.proof_obligations or []),
        ]).lower()
        explicit = any(tok.lower() in blob for tok in _EXPLICIT) or bool(h.instance_maps)
        if h.hypothesis_type in {"divided_difference", "confluent_representation"} and not explicit:
            continue
        hits.append(h.hypothesis_type)
    return {"pass": bool(hits), "types": hits}


def g2_formalization(hyps: list[LLMStructureHypothesis]) -> dict[str, Any]:
    """H_repr-like: latent + member maps + nodes or operators."""
    ok = []
    for h in hyps:
        if h.parse_status != OK:
            continue
        if h.hypothesis_type not in G1_TYPES:
            continue
        has_maps = bool(h.instance_maps) and bool(h.target_members)
        has_latent = bool((h.latent_object or "").strip())
        if has_maps and has_latent:
            ok.append(h.hypothesis_type)
    return {"pass": bool(ok), "types": ok}


def g3_compile(compiles: list) -> dict[str, Any]:
    n_ok = sum(c.n_ok for c in compiles)
    n_fail = sum(c.n_fail for c in compiles)
    return {"pass": n_ok > 0, "n_ok": n_ok, "n_fail": n_fail}


def g4_certify(verdicts: list[str]) -> dict[str, Any]:
    z = sum(1 for v in verdicts if v == "ZERO")
    nz = sum(1 for v in verdicts if v == "NONZERO")
    unk = sum(1 for v in verdicts if v == "UNKNOWN")
    return {
        "pass": z > 0 and nz == 0 and unk == 0,
        "n_zero": z, "n_nonzero": nz, "n_unknown": unk,
        "partial_zero": z > 0,
    }
