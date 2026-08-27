"""Quality flags including UNNECESSARY_STRUCTURE. Not a verifier."""
from __future__ import annotations

import re
from typing import Iterable

from research.llm_abstraction.schema import LLMStructureHypothesis, UNNECESSARY_STRUCTURE

UNNECESSARY_MARKERS = (
    r"interpolat",
    r"geodesic",
    r"latent space",
    r"latent code",
    r"decoder",
    r"procrustes",
    r"fiber bundle",
    r"neural",
    r"generative model",
    r"learned latent",
    r"affine combination",
    r"\bz \* .+\+\s*\(1\s*-\s*z\)",
    r"\(1-z\).+\+\s*z",
)

_SHALLOW_TMPL = re.compile(
    r"^(I\*)?mu\*theta\d*$|^theta\d*(\*theta\d*)*$",
    re.I,
)


def flag_unnecessary(hyp: LLMStructureHypothesis) -> list[str]:
    blob = " ".join([
        hyp.rationale or "",
        hyp.construction_plan or "",
        hyp.latent_object or "",
        " ".join(hyp.proof_obligations or []),
    ]).lower()
    flags = []
    for pat in UNNECESSARY_MARKERS:
        if re.search(pat, blob, flags=re.I):
            flags.append(UNNECESSARY_STRUCTURE)
            break
    tmpl = re.sub(r"\s+", "", hyp.latent_object or "")
    if _SHALLOW_TMPL.match(tmpl) or tmpl in {"theta0", "theta0*theta1"}:
        flags.append("shallow")
    # Tautological: latent is exactly one member and no operator.
    members = [re.sub(r"\s+", "", m) for m in hyp.target_members]
    if tmpl in members and hyp.hypothesis_type in {
        "master_function", "parameterized_family", "generating_function",
    }:
        flags.append("tautological")
    return list(dict.fromkeys(flags))


def looks_representation_change(hyp: LLMStructureHypothesis) -> bool:
    from research.llm_abstraction.schema import REPRESENTATION_TYPES
    if hyp.hypothesis_type in REPRESENTATION_TYPES:
        return True
    latent = hyp.latent_object or ""
    # new head heuristic: a named call not appearing in members
    heads = set(re.findall(r"([A-Za-z][A-Za-z0-9_]*)\s*\(", latent))
    member_blob = " ".join(hyp.target_members)
    novel = [h for h in heads if h not in member_blob
             and h not in {"sin", "cos", "exp", "log", "sqrt", "polygamma",
                           "Piecewise", "Sum", "Product", "Abs", "I"}]
    return bool(novel)
