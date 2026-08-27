"""Hypothesis-to-source grounding. No fuzzy string replace.

Only EXACT_BIND and UNIQUE_STRUCTURAL_BIND may enter the verifier.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from research.llm_abstraction.constructor import parse_flex
from research.obligation_ir.source_index import SourceIndex, SourceNode

EXACT_BIND = "EXACT_BIND"
UNIQUE_STRUCTURAL_BIND = "UNIQUE_STRUCTURAL_BIND"
AMBIGUOUS_BIND = "AMBIGUOUS_BIND"
NO_BIND = "NO_BIND"

_H_CALL = re.compile(r"h[12]\([^)]+\)")


@dataclass
class Binding:
    alias: str
    confidence: str
    gid: str = ""
    sol_node_id: str = ""
    text: str = ""
    srepr: str = ""
    kind: str = ""
    cond: str = ""
    evidence: str = ""
    candidate_gids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def admissible(self) -> bool:
        return self.confidence in {EXACT_BIND, UNIQUE_STRUCTURAL_BIND} and bool(self.text)


def _fp_cond(cond: str) -> str:
    s = (cond or "").lower().replace(" ", "")
    if s in {"true", "s.true", "generic", "off", "off-diagonal", "offdiagonal"}:
        return "true"
    # epsilon(a)=epsilon(b) or Eq(a,b) or a=b
    pairs = re.findall(
        r"epsilon\(([a-z]+)\)\s*(?:=|->|→)\s*epsilon\(([a-z]+)\)", s
    )
    if not pairs:
        eqs = re.findall(r"eq\(([a-z]+),([a-z]+)\)", s)
        pairs = eqs
    if not pairs and re.fullmatch(r"([a-z])=\1", s):
        return "true"  # nonsense
    if "ell" in s and "m" in s and "n" in s and ("&" in s or "and" in s or s.count("=") >= 2 or "all" in s):
        return "eq_ell_m_n"
    names = []
    for a, b in pairs:
        names.append(tuple(sorted((a, b))))
    if not names:
        if "eq(m,n)" in s or "m=n" in s or "coincide:m=n" in s.replace(" ", ""):
            return "eq_m_n"
        if "eq(ell,n)" in s or "ell=n" in s:
            return "eq_ell_n"
        if "eq(ell,m)" in s or "ell=m" in s:
            return "eq_ell_m"
        if s in {"true"}:
            return "true"
        return s
    if ("ell", "m") in names or ("m", "ell") in names:
        if ("m", "n") in names:
            return "eq_ell_m_n"
        return "eq_ell_m"
    if ("ell", "n") in names:
        return "eq_ell_n"
    if ("m", "n") in names:
        return "eq_m_n"
    return s


def _node_cond_fp(node: SourceNode) -> str:
    c = node.cond
    if c in {"True", "true", ""}:
        return "true" if node.kind == "piecewise_branch" and (c.lower() == "true" or c == "") else (c or "")
    s = c.replace(" ", "").lower()
    if "true" == s:
        return "true"
    # srepr Equality(Symbol('m', real=True), Symbol('n', real=True))
    syms = re.findall(r"symbol\('([a-z]+)'", s)
    if "and" in s or "&" in s:
        if set(syms) >= {"ell", "m", "n"}:
            return "eq_ell_m_n"
    if set(syms) == {"m", "n"} or set(syms) == {"n", "m"}:
        return "eq_m_n"
    if set(syms) == {"ell", "n"}:
        return "eq_ell_n"
    if set(syms) == {"ell", "m"}:
        return "eq_ell_m"
    return _fp_cond(c)


def _h_set(text: str) -> frozenset[str]:
    return frozenset(_H_CALL.findall(text.replace(" ", ""))) if False else frozenset(
        re.findall(r"h[12]\([^)]+\)", text)
    )


def _normalize_h(s: str) -> frozenset[str]:
    calls = re.findall(r"h[12]\(\s*[^)]+\)", s)
    out = []
    for c in calls:
        c2 = re.sub(r"\s+", "", c)
        out.append(c2)
    return frozenset(out)


def extract_h_fingerprint(member: str, theta: dict, latent: str) -> frozenset[str]:
    blobs = [member or "", latent or ""]
    for k in ("h_factor", "h_product", "h1_factors", "kernel_attachments", "h_factors"):
        v = theta.get(k)
        if v:
            blobs.append(str(v))
    fp = frozenset()
    for b in blobs:
        got = _normalize_h(b)
        if len(got) >= 2:
            return got
        if got:
            fp = got
    return fp


def extract_cond_hint(alias: str, theta: dict) -> str:
    for k in ("collision", "coincide", "limit", "confluent_case"):
        if k in theta:
            return _fp_cond(str(theta[k]))
    a = alias.lower()
    if any(x in a for x in ("_true", "off", "generic", "nonsing")):
        return "true"
    if "all_equal" in a or "eq_all" in a or "ell,m)&eq(m,n)" in a:
        return "eq_ell_m_n"
    if "eq_elln" in a or "eq_ell_n" in a or "ell,n)" in a:
        return "eq_ell_n"
    if "eq_ellm" in a or "eq_ell_m" in a:
        return "eq_ell_m"
    if "eq_mn" in a or "eq_m_n" in a or "diag" in a or "diagonal" in a:
        return "eq_m_n"
    return ""


def _one_or_amb(alias: str, hits: list[SourceNode], evidence: str) -> Binding:
    if len(hits) == 1:
        n = hits[0]
        return Binding(
            alias=alias,
            confidence=UNIQUE_STRUCTURAL_BIND,
            gid=n.gid,
            sol_node_id=n.sol_node_id,
            text=n.text,
            srepr=n.srepr,
            kind=n.kind,
            cond=n.cond,
            evidence=evidence,
        )
    if len(hits) > 1:
        return Binding(
            alias=alias,
            confidence=AMBIGUOUS_BIND,
            candidate_gids=[n.gid for n in hits],
            evidence=evidence + f" n={len(hits)}",
            kind=hits[0].kind,
        )
    return Binding(alias=alias, confidence=NO_BIND, evidence=evidence + " none")


def bind_alias(
    alias: str,
    index: SourceIndex,
    *,
    theta: Optional[dict] = None,
    latent: str = "",
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> Binding:
    theta = theta or {}
    if re.fullmatch(r"[NG]\d{4}", alias.strip()):
        for n in index.nodes:
            if n.sol_node_id == alias or n.gid == alias:
                return Binding(
                    alias=alias, confidence=EXACT_BIND, gid=n.gid,
                    sol_node_id=n.sol_node_id, text=n.text, srepr=n.srepr,
                    kind=n.kind, cond=n.cond, evidence="node_id_exact",
                )
        return Binding(alias=alias, confidence=NO_BIND, evidence="unknown_node_id")
    # 1. exact parse
    parsed = parse_flex(alias, symbols or [], functions or [])
    if parsed is not None:
        key = sympy.srepr(parsed)
        hits = index.by_srepr.get(key) or []
        if len(hits) == 1:
            n = hits[0]
            return Binding(
                alias=alias, confidence=EXACT_BIND, gid=n.gid,
                sol_node_id=n.sol_node_id, text=n.text, srepr=n.srepr,
                kind=n.kind, cond=n.cond, evidence="srepr_exact",
            )
        if len(hits) > 1:
            return Binding(
                alias=alias, confidence=AMBIGUOUS_BIND,
                candidate_gids=[n.gid for n in hits],
                evidence="srepr_exact_multiple",
            )
        text_hits = [n for n in index.nodes if n.text == str(parsed)]
        if len(text_hits) == 1:
            n = text_hits[0]
            return Binding(
                alias=alias, confidence=EXACT_BIND, gid=n.gid,
                sol_node_id=n.sol_node_id, text=n.text, srepr=n.srepr,
                kind=n.kind, evidence="text_exact",
            )
    # 2. h-factor unique sum/branch
    hf = extract_h_fingerprint(alias, theta, latent)
    cond = extract_cond_hint(alias, theta)
    if hf:
        def _sum_h(n: SourceNode) -> frozenset[str]:
            return frozenset(re.sub(r"\s+", "", h) for h in n.h_factors)
        sums = [n for n in index.nodes if n.kind == "sum" and hf <= _sum_h(n)]
        exact_sums = [n for n in index.nodes if n.kind == "sum" and _sum_h(n) == hf]
        if exact_sums:
            sums = exact_sums
        if cond:
            branches = [
                n for n in index.nodes
                if n.kind == "piecewise_branch"
                and _node_cond_fp(n) == cond
                and n.parent_gid
            ]
            # restrict to piecewise children of matching sums
            pw_of = {}
            for n in index.nodes:
                if n.kind == "piecewise":
                    pw_of[n.gid] = n.parent_gid
            sum_ids = {s.gid for s in sums} if sums else set()
            if sum_ids:
                branches = [b for b in branches if pw_of.get(b.parent_gid) in sum_ids]
            return _one_or_amb(alias, branches, f"h_factor+cond:{cond}")
        if sums:
            return _one_or_amb(alias, sums, "h_factor_unique_sum")
    # 3. cond-only: unique among ALL branches only if exactly one PW in whole expr
    if cond:
        branches = [n for n in index.nodes if n.kind == "piecewise_branch" and _node_cond_fp(n) == cond]
        pws = [n for n in index.nodes if n.kind == "piecewise"]
        if len(pws) == 1:
            return _one_or_amb(alias, branches, f"single_pw+cond:{cond}")
        return _one_or_amb(alias, branches, f"cond_only:{cond}")
    return Binding(alias=alias, confidence=NO_BIND, evidence="no_exact_no_fingerprint")


def bind_hypothesis_members(
    hyp: dict,
    index: SourceIndex,
    *,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> list[Binding]:
    latent = hyp.get("latent_object") or ""
    maps = hyp.get("instance_maps") or []
    members = hyp.get("target_members") or []
    out = []
    seen = set()
    for im in maps:
        if not isinstance(im, dict):
            continue
        alias = str(im.get("member") or "")
        if not alias or alias in seen:
            continue
        seen.add(alias)
        theta = im.get("theta") if isinstance(im.get("theta"), dict) else {}
        out.append(bind_alias(
            alias, index, theta=theta, latent=latent,
            symbols=symbols, functions=functions,
        ))
    for m in members:
        if m in seen:
            continue
        seen.add(m)
        out.append(bind_alias(
            str(m), index, theta={}, latent=latent,
            symbols=symbols, functions=functions,
        ))
    return out
