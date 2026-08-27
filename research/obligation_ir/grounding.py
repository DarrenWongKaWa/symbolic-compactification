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


UNIQUE_BY_EXPLICIT_EXPR = "UNIQUE_BY_EXPLICIT_EXPR"
UNIQUE_BY_SOL_ID = "UNIQUE_BY_SOL_ID"
UNIQUE_BY_LOCAL_FINGERPRINT = "UNIQUE_BY_LOCAL_FINGERPRINT"


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
    unique_kind: str = ""
    n_candidates: int = 0
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


def _sum_h(n: SourceNode) -> frozenset[str]:
    return frozenset(re.sub(r"\s+", "", h) for h in n.h_factors)


def _arity_of_node(n: SourceNode) -> int:
    blob = " ".join(n.h_factors)
    return 3 if re.search(r"\bell\b", blob) else 2


def hyp_blob(hyp: dict) -> str:
    """All text belonging to this hypothesis only. No sibling hyps."""
    parts = [
        hyp.get("latent_object") or "",
        hyp.get("rationale") or "",
        hyp.get("construction_plan") or "",
        " ".join(hyp.get("proof_obligations") or []),
        " ".join(hyp.get("target_members") or []),
    ]
    for im in hyp.get("instance_maps") or []:
        if isinstance(im, dict):
            parts.append(str(im.get("member") or ""))
            th = im.get("theta") or {}
            if isinstance(th, dict):
                parts.append(json_dump_theta(th))
    return "\n".join(parts)


def json_dump_theta(th: dict) -> str:
    bits = []
    for k, v in th.items():
        bits.append(f"{k}={v}")
    return " ".join(bits)


def _arity_from_text(t: str) -> int:
    t = (t or "").lower()
    if "three-index" in t or "triple sum" in t or "triple-sum" in t or "epsilon(ell)" in t:
        return 3
    if "two-index" in t or "double sum" in t or "double-sum" in t:
        return 2
    return 0


def _arity_hint(alias: str, theta: dict, blob: str) -> int:
    nodes = theta.get("nodes")
    if isinstance(nodes, list):
        if any("ell" in str(x) for x in nodes):
            return 3
        if len(nodes) >= 3:
            return 3
        if len(nodes) == 2:
            return 2
    local = _arity_from_text(" ".join([alias, str(theta)]))
    if local:
        return local
    return _arity_from_text(blob[:1500])


def _label_set(theta: dict, local: str) -> frozenset[str]:
    labs = set()
    v = theta.get("external_labels")
    if isinstance(v, list):
        labs.update(str(x) for x in v if str(x) in {"b", "c"})
    return frozenset(labs)


def _hsets_mentioned(text: str, index: SourceIndex) -> list[frozenset[str]]:
    blob = _normalize_h(text)
    found = []
    for n in index.nodes:
        if n.kind != "sum":
            continue
        hs = _sum_h(n)
        if hs and hs <= blob:
            found.append(hs)
    # unique
    uniq = []
    for hs in found:
        if hs not in uniq:
            uniq.append(hs)
    return uniq


def intersect_branches(
    index: SourceIndex,
    *,
    branch: str,
    arity: int,
    hset: frozenset[str],
    labels: frozenset[str],
) -> list[SourceNode]:
    if not branch and arity not in {2, 3} and not hset and not labels:
        return []
    pool = [n for n in index.nodes if n.kind == "piecewise_branch"]
    if branch:
        pool = [n for n in pool if _node_cond_fp(n) == branch]
    if arity in {2, 3}:
        pool = [n for n in pool if _arity_of_node(n) == arity]
    if hset:
        pool = [n for n in pool if hset <= _sum_h(n) or hset == _sum_h(n)]
    if labels:
        pool = [n for n in pool if all(
            re.search(rf"\b{re.escape(lab)}\b", " ".join(n.h_factors))
            for lab in labels
        )]
    return pool


def _unique_kind(evidence: str, h_local: bool, sol: bool) -> str:
    if sol:
        return UNIQUE_BY_SOL_ID
    if h_local or "h_factor" in evidence:
        return UNIQUE_BY_EXPLICIT_EXPR
    return UNIQUE_BY_LOCAL_FINGERPRINT


def _one_or_amb(alias: str, hits: list[SourceNode], evidence: str, *,
                unique_kind: str = "") -> Binding:
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
            unique_kind=unique_kind or UNIQUE_BY_LOCAL_FINGERPRINT,
            n_candidates=1,
        )
    if len(hits) > 1:
        return Binding(
            alias=alias,
            confidence=AMBIGUOUS_BIND,
            candidate_gids=[n.gid for n in hits],
            evidence=evidence + f" n={len(hits)}",
            kind=hits[0].kind,
            n_candidates=len(hits),
        )
    return Binding(alias=alias, confidence=NO_BIND, evidence=evidence + " none", n_candidates=0)


def bind_alias(
    alias: str,
    index: SourceIndex,
    *,
    theta: Optional[dict] = None,
    latent: str = "",
    hyp: Optional[dict] = None,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> Binding:
    theta = theta or {}
    blob = hyp_blob(hyp) if hyp else latent
    if re.fullmatch(r"[NG]\d{4}", alias.strip()):
        for n in index.nodes:
            if n.sol_node_id == alias or n.gid == alias:
                return Binding(
                    alias=alias, confidence=EXACT_BIND, gid=n.gid,
                    sol_node_id=n.sol_node_id, text=n.text, srepr=n.srepr,
                    kind=n.kind, cond=n.cond, evidence="node_id_exact",
                    unique_kind=UNIQUE_BY_SOL_ID, n_candidates=1,
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
                unique_kind=UNIQUE_BY_EXPLICIT_EXPR, n_candidates=1,
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
                unique_kind=UNIQUE_BY_EXPLICIT_EXPR, n_candidates=1,
            )
    # Intra-hyp constraint intersection on Piecewise branches / sums.
    local = " ".join([alias, json_dump_theta(theta)])
    local_h = extract_h_fingerprint(alias, theta, "")  # member+map only
    global_hsets = _hsets_mentioned(blob, index) if blob else []
    hset = local_h
    h_local = bool(local_h)
    if not hset and len(global_hsets) == 1:
        hset = global_hsets[0]
        h_local = False
    cond = extract_cond_hint(alias, theta)
    arity = _arity_hint(alias, theta, blob)
    labels = _label_set(theta, local)
    hits = intersect_branches(
        index, branch=cond, arity=arity, hset=hset, labels=labels,
    )
    if hset and not cond:
        sums = [n for n in index.nodes if n.kind == "sum" and (hset <= _sum_h(n) or hset == _sum_h(n))]
        uk = UNIQUE_BY_EXPLICIT_EXPR if h_local else UNIQUE_BY_LOCAL_FINGERPRINT
        return _one_or_amb(alias, sums, "constraint_sum", unique_kind=uk)
    ev = f"C_fn={int(bool(hset))}|C_ar={arity}|C_br={cond or '-'}|C_lab={''.join(sorted(labels))}|n0={len(hits)}"
    uk = UNIQUE_BY_EXPLICIT_EXPR if h_local else UNIQUE_BY_LOCAL_FINGERPRINT
    if hits or cond or hset or arity or labels:
        return _one_or_amb(alias, hits, ev, unique_kind=uk)
    return Binding(alias=alias, confidence=NO_BIND, evidence="no_exact_no_fingerprint", n_candidates=0)


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
            alias, index, theta=theta, latent=latent, hyp=hyp,
            symbols=symbols, functions=functions,
        ))
    for m in members:
        if m in seen:
            continue
        seen.add(m)
        out.append(bind_alias(
            str(m), index, theta={}, latent=latent, hyp=hyp,
            symbols=symbols, functions=functions,
        ))
    return out
