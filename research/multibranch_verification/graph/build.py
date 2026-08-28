"""Branch graphs for frozen 5-branch / Hermite families.

Evaluation-only. Nodes are G#### members. Edges come from hypothesis
operators and piecewise branch conditions (and generic confluence of
coinciding nodes). Does not adjudicate FAMILY_ZERO. No LLM.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Optional

from research.multibranch_verification.schema import (
    EDGE_RELATIONS,
    FAMILY_UNKNOWN,
    ConfluentFamilyCertificate,
    LocalEdge,
)

ROOT = Path(__file__).resolve().parents[3]
FROZEN_PATH = Path(__file__).resolve().parents[1] / "FROZEN_INPUTS_V2.json"
MAP_PATH = (
    ROOT / "research" / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
)
OUT = Path(__file__).resolve().parent / "BRANCH_GRAPHS.json"

_EQ_RE = re.compile(
    r"Equality\(\s*Symbol\('([^']+)'(?:,\s*real=True)?\)\s*,\s*"
    r"Symbol\('([^']+)'(?:,\s*real=True)?\)\s*\)"
)
_EPS_RE = re.compile(r"epsilon\(([A-Za-z]+)\)")
_ARROW_RE = re.compile(r"([A-Za-z()]+)\s*->\s*([A-Za-z()]+)")
_INDEX_NAMES = frozenset({"ell", "m", "n"})
_XYZ_DEFAULT = {"x": "epsilon(m)", "y": "epsilon(n)", "z": "epsilon(ell)"}
_PREFERRED_DIR = {
    frozenset({"m", "n"}): ("m", "n"),
    frozenset({"ell", "n"}): ("ell", "n"),
    frozenset({"ell", "m"}): ("ell", "m"),
}
_RESERVED_ARG_KEYS = frozenset(
    {
        "source",
        "target",
        "var",
        "to",
        "limits",
        "constraint",
        "substitution",
        "compose",
        "kind",
        "member_id",
        "member",
    }
)
_NUMBERED_IO = re.compile(r"^(source|target)(\d+)$")

ONE_PARAMETER = "one_parameter_confluence"
REPEATED_NODE = "repeated_node_confluence"
SUBSTITUTION = "substitution"
LIMIT = "limit"


def _is_true(cond: str) -> bool:
    return (cond or "").strip() == "True"


def _parse_equalities(cond: str) -> list[tuple[str, str]]:
    """Return undirected index equalities from a sympy srepr cond."""
    if _is_true(cond):
        return []
    out: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    for a, b in _EQ_RE.findall(cond or ""):
        if a == b:
            continue
        key = frozenset({a, b})
        if key in seen:
            continue
        seen.add(key)
        out.append((a, b))
    return out


def _dir_pair(a: str, b: str) -> tuple[str, str]:
    pref = _PREFERRED_DIR.get(frozenset({a, b}))
    if pref:
        return pref
    return (a, b) if a <= b else (b, a)


def _as_eps(token: str, xyz: dict[str, str]) -> str:
    raw = (token or "").strip()
    if not raw:
        return raw
    if raw in xyz:
        return xyz[raw]
    if raw.startswith("epsilon(") and raw.endswith(")"):
        return raw
    inner = _EPS_RE.fullmatch(raw)
    if inner:
        return f"epsilon({inner.group(1)})"
    return f"epsilon({raw})"


def _xyz_map(reconstruction_rule: str) -> dict[str, str]:
    found: list[str] = []
    for name in _EPS_RE.findall(reconstruction_rule or ""):
        if name not in found:
            found.append(name)
    if len(found) >= 3:
        return {
            "x": f"epsilon({found[0]})",
            "y": f"epsilon({found[1]})",
            "z": f"epsilon({found[2]})",
        }
    return dict(_XYZ_DEFAULT)


def _pairs_from_equalities(eqs: list[tuple[str, str]], xyz: dict[str, str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for a, b in eqs:
        src, tgt = _dir_pair(a, b)
        item = (_as_eps(src, xyz), _as_eps(tgt, xyz))
        if item not in seen:
            seen.add(item)
            pairs.append(item)
    return pairs


def _is_reserved_key(key: str) -> bool:
    if key in _RESERVED_ARG_KEYS:
        return True
    return _NUMBERED_IO.fullmatch(key) is not None


def _looks_index_token(token: str, xyz: dict[str, str]) -> bool:
    raw = (token or "").strip()
    if raw in xyz or raw in _INDEX_NAMES:
        return True
    if raw.startswith("epsilon(") and raw.endswith(")"):
        return True
    return False


def _append_pair(
    pairs: list[tuple[str, str]],
    src: str,
    tgt: str,
    xyz: dict[str, str],
) -> None:
    if not src or not tgt:
        return
    item = (_as_eps(src, xyz), _as_eps(tgt, xyz))
    if item not in pairs:
        pairs.append(item)


def _pairs_from_args(args: dict[str, Any], xyz: dict[str, str]) -> list[tuple[str, str]]:
    if not isinstance(args, dict):
        return []
    pairs: list[tuple[str, str]] = []
    if args.get("source") is not None and args.get("target") is not None:
        _append_pair(pairs, str(args["source"]), str(args["target"]), xyz)
    i = 1
    while i <= 8:
        s = args.get(f"source{i}")
        t = args.get(f"target{i}")
        if s is None and t is None:
            break
        if s is not None and t is not None:
            _append_pair(pairs, str(s), str(t), xyz)
        i += 1
    if args.get("var") is not None and args.get("to") is not None:
        _append_pair(pairs, str(args["var"]), str(args["to"]), xyz)
    limits = args.get("limits")
    if isinstance(limits, list):
        for item in limits:
            if not isinstance(item, dict):
                continue
            nested = _pairs_from_args(item, xyz)
            for p in nested:
                if p not in pairs:
                    pairs.append(p)
    constraint = args.get("constraint")
    if isinstance(constraint, str) and constraint.strip():
        for src, tgt in _ARROW_RE.findall(constraint):
            _append_pair(pairs, src, tgt, xyz)
    for key, val in args.items():
        if _is_reserved_key(str(key)):
            continue
        if not isinstance(val, str):
            continue
        if _looks_index_token(str(key), xyz) and _looks_index_token(val, xyz):
            _append_pair(pairs, str(key), val, xyz)
    return pairs


def _compose_steps(args: dict[str, Any]) -> list[dict[str, Any]]:
    raw = args.get("compose") if isinstance(args, dict) else None
    if not isinstance(raw, list):
        return []
    return [step for step in raw if isinstance(step, dict)]


def _limit_ops(operators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for op in operators:
        kind = str(op.get("kind") or "")
        mid = str(op.get("member_id") or op.get("member") or "")
        args = op.get("args") if isinstance(op.get("args"), dict) else {}
        if kind == LIMIT:
            out.append({"member_id": mid, "kind": LIMIT, "args": args})
        elif kind == "other":
            for step in _compose_steps(args):
                if str(step.get("kind") or "") == LIMIT:
                    step_args = step.get("args") if isinstance(step.get("args"), dict) else {}
                    out.append({"member_id": mid, "kind": LIMIT, "args": step_args})
    return out


def _substitution_map(args: dict[str, Any]) -> dict[str, str]:
    if not isinstance(args, dict):
        return {}
    nested = args.get("substitution")
    blob = nested if isinstance(nested, dict) else args
    out: dict[str, str] = {}
    reserved = _RESERVED_ARG_KEYS | {"limits", "constraint"}
    for k, v in blob.items():
        if str(k) in reserved or _NUMBERED_IO.fullmatch(str(k)):
            continue
        if isinstance(v, (str, int)):
            out[str(k)] = str(v)
    return out


def _join_pairs(pairs: list[tuple[str, str]]) -> tuple[str, str]:
    ordered = sorted(pairs, key=lambda p: (p[0], p[1]))
    return (
        ",".join(p[0] for p in ordered),
        ",".join(p[1] for p in ordered),
    )


def _relation_for_pairs(pairs: list[tuple[str, str]]) -> str:
    if len(pairs) >= 2:
        return REPEATED_NODE
    return ONE_PARAMETER


def _max_class_size(eqs: list[tuple[str, str]]) -> int:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in eqs:
        union(a, b)
    if not parent:
        return 1
    counts: dict[str, int] = defaultdict(int)
    for node in parent:
        counts[find(node)] += 1
    return max(counts.values())


def _overlay_conds(
    members: list[dict[str, Any]],
    map_members: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in members:
        rec = dict(m)
        gid = str(m.get("member_id") or "")
        mapped = map_members.get(gid)
        if mapped and (mapped.get("cond") or ""):
            rec["cond"] = mapped["cond"]
        out.append(rec)
    return out


def _identity_member(operators: list[dict[str, Any]]) -> str:
    for op in operators:
        if str(op.get("kind") or "") == "identity":
            return str(op.get("member_id") or op.get("member") or "")
    return ""


def _edge_key(source: str, target: str, relation: str) -> tuple[str, str, str]:
    return (source, target, relation)


class _EdgeAcc:
    def __init__(self, family_id: str) -> None:
        self.family_id = family_id
        self._edges: dict[tuple[str, str, str], LocalEdge] = {}

    def add(
        self,
        *,
        source: str,
        target: str,
        relation: str,
        variable: str = "",
        target_value: str = "",
        provenance: str,
    ) -> None:
        if not source or not target or source == target:
            return
        if relation not in EDGE_RELATIONS:
            return
        key = _edge_key(source, target, relation)
        existing = self._edges.get(key)
        if existing is None:
            self._edges[key] = LocalEdge(
                source=source,
                target=target,
                relation=relation,
                variable=variable,
                target_value=target_value,
                obligation_id=f"{self.family_id}:{source}->{target}:{relation}",
                verdict="UNKNOWN",
                provenance=provenance,
            )
            return
        bits = [b for b in existing.provenance.split("+") if b]
        if provenance and provenance not in bits:
            bits.append(provenance)
            existing.provenance = "+".join(bits)
        # Operators own source/target names when they state them.
        if variable and (
            (provenance.startswith("operator:") or not existing.variable)
        ):
            existing.variable = variable
            existing.target_value = target_value

    def to_list(self) -> list[LocalEdge]:
        return [self._edges[k] for k in sorted(self._edges)]


def build_family(
    hyp: dict[str, Any],
    map_row: Optional[dict[str, Any]] = None,
) -> ConfluentFamilyCertificate:
    member_ids = [str(x) for x in (hyp.get("member_ids") or [])]
    raw_members = list(hyp.get("members") or [])
    map_members = {}
    if map_row:
        map_members = {
            str(m.get("member_id") or ""): m
            for m in (map_row.get("members") or [])
            if isinstance(m, dict)
        }
    members = _overlay_conds(raw_members, map_members)
    by_id = {str(m.get("member_id") or ""): m for m in members}
    operators = [o for o in (hyp.get("operators") or []) if isinstance(o, dict)]
    xyz = _xyz_map(str(hyp.get("reconstruction_rule") or ""))
    claimed = str(hyp.get("claimed_type") or "")
    family_id = str(hyp.get("family_id") or "")
    acc = _EdgeAcc(family_id)

    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for m in members:
        by_parent[str(m.get("parent_gid") or "")].append(m)

    generic_members = [
        str(m.get("member_id") or "") for m in members if _is_true(str(m.get("cond") or ""))
    ]
    degenerate_members = [gid for gid in member_ids if gid not in generic_members]

    for _parent, group in by_parent.items():
        trues = [m for m in group if _is_true(str(m.get("cond") or ""))]
        degenerates = [m for m in group if not _is_true(str(m.get("cond") or ""))]
        for src_m in trues:
            src = str(src_m.get("member_id") or "")
            for tgt_m in degenerates:
                tgt = str(tgt_m.get("member_id") or "")
                eqs = _parse_equalities(str(tgt_m.get("cond") or ""))
                if not eqs:
                    continue
                pairs = _pairs_from_equalities(eqs, xyz)
                relation = _relation_for_pairs(pairs)
                variable, target_value = _join_pairs(pairs) if pairs else ("", "")
                acc.add(
                    source=src,
                    target=tgt,
                    relation=relation,
                    variable=variable,
                    target_value=target_value,
                    provenance="cond",
                )

    identity = _identity_member(operators)
    for op in _limit_ops(operators):
        tgt = str(op.get("member_id") or "")
        rec = by_id.get(tgt)
        if rec is None:
            continue
        if _is_true(str(rec.get("cond") or "")):
            continue
        parent = str(rec.get("parent_gid") or "")
        src = ""
        for cand in by_parent.get(parent, []):
            if _is_true(str(cand.get("cond") or "")):
                src = str(cand.get("member_id") or "")
                break
        if not src:
            src = identity
        args = op.get("args") if isinstance(op.get("args"), dict) else {}
        pairs = _pairs_from_args(args, xyz)
        if not pairs:
            pairs = _pairs_from_equalities(_parse_equalities(str(rec.get("cond") or "")), xyz)
        if not pairs:
            continue
        relation = _relation_for_pairs(pairs)
        variable, target_value = _join_pairs(pairs)
        acc.add(
            source=src,
            target=tgt,
            relation=relation,
            variable=variable,
            target_value=target_value,
            provenance="operator:limit",
        )

    for op in operators:
        if str(op.get("kind") or "") != SUBSTITUTION:
            continue
        tgt = str(op.get("member_id") or op.get("member") or "")
        if not tgt or tgt not in by_id:
            continue
        src = identity
        if not src or src == tgt:
            for gid in generic_members:
                if gid != tgt:
                    src = gid
                    break
        args = op.get("args") if isinstance(op.get("args"), dict) else {}
        subst = _substitution_map(args)
        variable = ""
        target_value = ""
        for a, b in sorted(subst.items()):
            if a != b:
                variable, target_value = a, b
                break
        acc.add(
            source=src,
            target=tgt,
            relation=SUBSTITUTION,
            variable=variable,
            target_value=target_value,
            provenance="operator:substitution",
        )

    edges = acc.to_list()
    deg_vars: list[str] = []
    seen_vars: set[str] = set()
    for e in edges:
        if e.relation not in {ONE_PARAMETER, REPEATED_NODE, LIMIT}:
            continue
        for blob in (e.variable, e.target_value):
            for part in blob.split(","):
                token = part.strip()
                if token and token not in seen_vars:
                    seen_vars.add(token)
                    deg_vars.append(token)
    deg_vars.sort()

    node_mult: dict[str, int] = {}
    for m in members:
        gid = str(m.get("member_id") or "")
        eqs = _parse_equalities(str(m.get("cond") or ""))
        node_mult[gid] = _max_class_size(eqs)

    return ConfluentFamilyCertificate(
        family_id=family_id,
        member_ids=member_ids,
        generic_members=generic_members,
        degenerate_members=degenerate_members,
        degeneracy_variables=deg_vars,
        node_multiplicities=node_mult,
        local_edges=edges,
        recurrence_obligations=[],
        consistency_obligations=[],
        assumptions=[
            "operator_or_cond_implied_edges_only",
            "no_adjudication",
        ],
        provenance=[
            "research/multibranch_verification/FROZEN_INPUTS_V2.json",
            "research/scalable_verification/guo_map/GUO_OBLIGATION_MAP.json",
            f"claimed_type:{claimed}",
            "no_llm",
        ],
        family_verdict=FAMILY_UNKNOWN,
    )


def _map_by_seed_index(blob: dict[str, Any]) -> dict[tuple[Any, Any], dict[str, Any]]:
    out: dict[tuple[Any, Any], dict[str, Any]] = {}
    for row in blob.get("hypotheses") or []:
        if isinstance(row, dict):
            out[(row.get("seed"), row.get("index"))] = row
    return out


def build_certificates(
    frozen: Optional[dict[str, Any]] = None,
    obligation_map: Optional[dict[str, Any]] = None,
) -> list[ConfluentFamilyCertificate]:
    frozen = frozen or json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    obligation_map = obligation_map or json.loads(MAP_PATH.read_text(encoding="utf-8"))
    mapped = _map_by_seed_index(obligation_map)
    certs: list[ConfluentFamilyCertificate] = []
    for hyp in frozen.get("hypotheses") or []:
        if not isinstance(hyp, dict):
            continue
        row = mapped.get((hyp.get("seed"), hyp.get("index")))
        certs.append(build_family(hyp, row))
    return certs


def build() -> dict[str, Any]:
    certs = build_certificates()
    return {
        "track": "V2",
        "agent": "V2-A",
        "evaluation_only": True,
        "does_not_adjudicate": True,
        "no_llm_calls": True,
        "source_frozen": "research/multibranch_verification/FROZEN_INPUTS_V2.json",
        "source_map": "research/scalable_verification/guo_map/GUO_OBLIGATION_MAP.json",
        "n_families": len(certs),
        "edge_relations": list(EDGE_RELATIONS),
        "families": [c.to_dict() for c in certs],
    }


def dumps(blob: dict[str, Any]) -> str:
    return json.dumps(blob, indent=2, ensure_ascii=True) + "\n"


def write(path: Optional[Path] = None) -> Path:
    dest = path or OUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = dumps(build())
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(dest)
    return dest


def load(path: Optional[Path] = None) -> dict[str, Any]:
    return json.loads((path or OUT).read_text(encoding="utf-8"))


def required_graph_connected(member_ids: Iterable[str], edges: list[LocalEdge]) -> bool:
    nodes = [str(x) for x in member_ids]
    if not nodes:
        return False
    adj: dict[str, set[str]] = {n: set() for n in nodes}
    for e in edges:
        if e.source in adj and e.target in adj:
            adj[e.source].add(e.target)
            adj[e.target].add(e.source)
    seen: set[str] = set()
    stack = [nodes[0]]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(adj[cur] - seen)
    return seen == set(nodes)


def main() -> None:
    dest = write()
    blob = json.loads(dest.read_text(encoding="utf-8"))
    print("wrote", dest, "n_families", blob.get("n_families"))


if __name__ == "__main__":
    main()
