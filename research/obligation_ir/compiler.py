"""Compile typed hypotheses / H_repr into Obligation IR. No promotion."""
from __future__ import annotations

import re
from typing import Any, Optional

from research.llm_abstraction.constructor import (
    _member,
    _op_name,
    _theta,
    parse_flex,
    symbolic_core,
)
from research.llm_abstraction.schema import LLMStructureHypothesis, OK
from research.obligation_ir.schema import (
    BASIS,
    COMPILE_FAILURE,
    COMPILE_OK,
    CONFLUENCE,
    CompileResult,
    DERIVATIVE,
    DIVIDED_DIFFERENCE,
    EQUALITY,
    LIMIT,
    Obligation,
    PERMUTATION,
    SUBSTITUTION,
)

_LIMIT_RE = re.compile(
    r"limit[_{\s]*([^}=]+?)(?:->|→)([^}\s]+)",
    re.I,
)


def _kind_for(op: str, htype: str) -> str:
    o = (op or "identity").lower()
    if any(k in o for k in ("d/d", "diff", "deriv")):
        return DERIVATIVE
    if "perm" in o or o == "swap":
        return PERMUTATION
    if "limit" in o:
        return LIMIT
    if "confluen" in o or htype == "confluent_representation":
        if "specialize" in o or o in {"identity", "specialize"}:
            # specialization of a template is SUBSTITUTION unless named confluence
            if htype == "confluent_representation" and "specialize" in o:
                return CONFLUENCE
        return CONFLUENCE if "confluen" in o else SUBSTITUTION
    if htype == "divided_difference":
        return DIVIDED_DIFFERENCE
    if htype == "basis_reduction":
        return BASIS
    if o in {"identity", "specialize", ""}:
        return SUBSTITUTION
    return EQUALITY


def _order(theta: dict) -> int:
    for k in ("order", "n_diff", "times"):
        if k in theta:
            try:
                return int(float(theta[k]))
            except (TypeError, ValueError):
                return 1
    return 1


def _nodes(theta: dict) -> list[str]:
    n = theta.get("nodes")
    if isinstance(n, list):
        return [str(x) for x in n]
    if isinstance(n, str) and n:
        return [n]
    return []


def compile_hypothesis(
    hyp: LLMStructureHypothesis,
    *,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> CompileResult:
    symbols = symbols or []
    functions = functions or []
    core = symbolic_core(hyp.latent_object or "")
    tmpl = parse_flex(hyp.latent_object or "", symbols, functions) if hyp.parse_status == OK else None
    maps = list(hyp.instance_maps or [])
    if not maps and hyp.target_members:
        maps = [{"member": m, "theta": {}, "O": "identity"} for m in hyp.target_members]
    out: list[Obligation] = []
    for imap in maps:
        member = _member(imap)
        theta = _theta(imap)
        raw_nodes: list[str] = []
        if isinstance(imap, dict):
            raw_th = imap.get("theta") if isinstance(imap.get("theta"), dict) else {}
            raw_nodes = _nodes(raw_th) if raw_th else _nodes(theta)
        op = _op_name(imap, hyp.operators, member)
        kind = _kind_for(op, hyp.hypothesis_type)
        parsed_member = parse_flex(member, symbols, functions)
        err = None
        status = COMPILE_OK
        if hyp.parse_status != OK:
            status, err = COMPILE_FAILURE, "hypothesis_parse_failure"
        elif tmpl is None:
            status, err = COMPILE_FAILURE, "unparseable_latent"
        elif parsed_member is None:
            status, err = COMPILE_FAILURE, "member_not_in_source"
        right = core
        if kind == DERIVATIVE:
            right = f"D^{_order(theta)}[{core}]"
        elif kind == PERMUTATION:
            right = f"permute[{core}]"
        elif kind == SUBSTITUTION:
            right = f"{core}|{theta}"
        out.append(Obligation(
            kind=kind,
            left=member,
            right=right,
            member=member,
            latent=core,
            operator=op,
            theta=theta,
            nodes=raw_nodes,
            order=_order(theta),
            compile_status=status,
            compile_error=err,
        ))
    # extra LIMIT rows from prose obligations (Guo confluence style)
    for text in hyp.proof_obligations or []:
        m = _LIMIT_RE.search(str(text))
        if not m:
            continue
        out.append(Obligation(
            kind=LIMIT,
            left=str(text),
            right="",
            member=str(text),
            latent=core,
            var=m.group(1).strip(),
            to=m.group(2).strip(),
            compile_status=COMPILE_FAILURE,
            compile_error="limit_sides_not_bound_to_source",
            source="proof_obligation_text",
        ))
    n_ok = sum(1 for o in out if o.compile_status == COMPILE_OK)
    n_fail = len(out) - n_ok
    return CompileResult(
        obligations=out,
        n_ok=n_ok,
        n_fail=n_fail,
        hypothesis_type=hyp.hypothesis_type,
        latent_core=core,
    )
