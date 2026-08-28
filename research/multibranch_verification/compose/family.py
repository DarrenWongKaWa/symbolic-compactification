"""Family composition for Track V2.

Pairwise ZERO is not FAMILY_ZERO. Majority vote is forbidden.

FAMILY_ZERO iff the required graph is connected, every required edge is
ZERO, every recurrence verdict is ZERO, path consistency is ZERO,
multiplicities are consistent, and the latent is compatible. Any required
NONZERO => FAMILY_NONZERO. Otherwise FAMILY_UNKNOWN.

Path consistency: two directed paths from A to B must compose to agreeing
operators. Disagreement of algebraic maps is NONZERO. Opaque / uncomposable
operators are UNKNOWN, never ZERO. Vacuous (≤1 path) is ZERO.

The global rule is ``schema.compose_family_verdict``; this module only
computes its inputs. Operators compose in a common name basis (no silent
push-forward of later targets through earlier identifications, and no
Hermite/limit rewrite).
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, replace
from itertools import combinations
from typing import Any, Iterable, Mapping, Optional, Sequence

from research.multibranch_verification.schema import (
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    ConfluentFamilyCertificate,
    LocalEdge,
    compose_family_verdict,
)

ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"

_ARROW_RE = re.compile(r"([^\s,;]+?)\s*(?:->|→)\s*([^\s,;]+)")
_SRC_N = re.compile(r"^source(\d+)$")
_TGT_N = re.compile(r"^target(\d+)$")

_ARG_RESERVED = frozenset(
    {
        "kind",
        "relation",
        "var",
        "to",
        "variable",
        "target_value",
        "constraint",
        "substitution",
        "compose",
        "operators",
        "steps",
        "multiplicity",
        "note",
        "source",
        "target",
        "verdict",
        "provenance",
        "obligation_id",
        "member_id",
        "args",
    }
)


@dataclass(frozen=True)
class ComposedOperator:
    """Name-map plus optional tagged/opaque payload."""

    mapping: tuple[tuple[str, str], ...] = ()
    tags: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = ()
    opaque: bool = False
    note: str = ""

    def as_map(self) -> dict[str, str]:
        return dict(self.mapping)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mapping": [list(p) for p in self.mapping],
            "tags": [[k, [list(p) for p in args]] for k, args in self.tags],
            "opaque": self.opaque,
            "note": self.note,
        }


@dataclass(frozen=True)
class PathConflict:
    src: str
    dst: str
    path_a: tuple[str, ...]
    path_b: tuple[str, ...]
    verdict: str
    note: str = ""


@dataclass(frozen=True)
class PathConsistencyResult:
    verdict: str
    path_verdicts: tuple[str, ...] = ()
    conflicts: tuple[PathConflict, ...] = ()
    truncated: bool = False
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "path_verdicts": list(self.path_verdicts),
            "conflicts": [asdict(c) for c in self.conflicts],
            "truncated": self.truncated,
            "note": self.note,
        }


@dataclass
class FamilyCompositionResult:
    family_verdict: str
    connected: bool
    multiplicities_consistent: bool
    latent_compatible: bool
    required_edge_verdicts: tuple[str, ...] = ()
    recurrence_verdicts: tuple[str, ...] = ()
    path_verdicts: tuple[str, ...] = ()
    path_consistency: Optional[PathConsistencyResult] = None
    notes: tuple[str, ...] = ()
    certificate: Optional[ConfluentFamilyCertificate] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "family_verdict": self.family_verdict,
            "connected": self.connected,
            "multiplicities_consistent": self.multiplicities_consistent,
            "latent_compatible": self.latent_compatible,
            "required_edge_verdicts": list(self.required_edge_verdicts),
            "recurrence_verdicts": list(self.recurrence_verdicts),
            "path_verdicts": list(self.path_verdicts),
            "path_consistency": (
                self.path_consistency.to_dict() if self.path_consistency else None
            ),
            "notes": list(self.notes),
        }
        if self.certificate is not None:
            d["certificate"] = self.certificate.to_dict()
        return d


def _normalize_verdict(value: Any) -> str:
    if value in (ZERO, NONZERO, UNKNOWN):
        return str(value)
    if value is None or value == "":
        return UNKNOWN
    return UNKNOWN


def _combine_verdicts(vs: Iterable[str]) -> str:
    seq = [_normalize_verdict(v) for v in vs]
    if any(v == NONZERO for v in seq):
        return NONZERO
    if any(v == UNKNOWN for v in seq):
        return UNKNOWN
    if seq and all(v == ZERO for v in seq):
        return ZERO
    return ZERO


def _edge_dict(edge: Any) -> dict[str, Any]:
    if isinstance(edge, LocalEdge):
        return edge.to_dict()
    if isinstance(edge, Mapping):
        return dict(edge)
    raise TypeError(f"edge must be LocalEdge or mapping, got {type(edge).__name__}")


def _is_edge_mapping(d: Mapping[str, Any]) -> bool:
    if "operator" in d and d.get("source") is not None and d.get("target") is not None:
        return True
    if "verdict" in d and "source" in d and "target" in d:
        return True
    if d.get("relation") and "source" in d and "target" in d:
        return True
    return False


def _mapping_from_args(args: Mapping[str, Any]) -> dict[str, str]:
    m: dict[str, str] = {}
    sub = args.get("substitution")
    if isinstance(sub, Mapping):
        for a, b in sub.items():
            m[str(a)] = str(b)
    var = args.get("variable") if args.get("variable") not in (None, "") else args.get("var")
    to = (
        args.get("target_value")
        if args.get("target_value") not in (None, "")
        else args.get("to")
    )
    if var not in (None, "") and to not in (None, ""):
        m[str(var)] = str(to)
    src, tgt = args.get("source"), args.get("target")
    if src not in (None, "") and tgt not in (None, ""):
        m[str(src)] = str(tgt)
    numbered: dict[str, dict[str, str]] = {}
    for key, val in args.items():
        ks = str(key)
        ms = _SRC_N.fullmatch(ks)
        mt = _TGT_N.fullmatch(ks)
        if ms:
            numbered.setdefault(ms.group(1), {})["s"] = str(val)
        elif mt:
            numbered.setdefault(mt.group(1), {})["t"] = str(val)
    for rec in numbered.values():
        if "s" in rec and "t" in rec:
            m[rec["s"]] = rec["t"]
    constraint = args.get("constraint")
    if isinstance(constraint, str):
        for mo in _ARROW_RE.finditer(constraint):
            m[mo.group(1)] = mo.group(2).rstrip(".")
    for key, val in args.items():
        ks = str(key)
        if ks in _ARG_RESERVED or _SRC_N.fullmatch(ks) or _TGT_N.fullmatch(ks):
            continue
        if isinstance(val, (str, int, float)) and not isinstance(val, bool):
            m[ks] = str(val)
    return m


def _tag_args(kind: str, args: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = []
    alias = {"var": "variable", "to": "target_value"}
    for k in ("variable", "var", "target_value", "to", "multiplicity"):
        if k in args and args[k] not in (None, ""):
            items.append((alias.get(k, k), str(args[k])))
    m = _mapping_from_args(args)
    for a, b in m.items():
        items.append((f"map:{a}", b))
    items.append(("kind", kind))
    return tuple(sorted(set(items)))


def _from_kind_args(kind: str, args: Mapping[str, Any]) -> ComposedOperator:
    k = (kind or "").strip()
    kl = k.lower()
    inner = args.get("compose")
    if isinstance(inner, (list, tuple)):
        return compose_operators(*inner)
    if kl == "compose":
        steps = args.get("operators") or args.get("steps") or ()
        return compose_operators(*steps)
    mapping = _mapping_from_args(args)
    canon_map = tuple(sorted(mapping.items()))
    if kl in {"identity", "id"}:
        return ComposedOperator()
    if kl in {"limit", "substitution", "one_parameter_confluence"}:
        if not mapping:
            return ComposedOperator(opaque=True, note=f"{kl}:empty_map")
        return ComposedOperator(mapping=canon_map)
    if kl == "repeated_node_confluence":
        tags = (("repeated_node_confluence", _tag_args(kl, args)),)
        return ComposedOperator(mapping=canon_map, tags=tags)
    if kl in {"derivative", "dd_recurrence", "hermite_dd_recurrence"}:
        return ComposedOperator(tags=((kl, _tag_args(kl, args)),))
    if not k and mapping:
        return ComposedOperator(mapping=canon_map)
    if not k and not mapping:
        return ComposedOperator()
    return ComposedOperator(
        mapping=canon_map,
        tags=((k, _tag_args(k, args)),),
        opaque=True,
        note=f"opaque:{k}",
    )


def _from_edge_dict(d: Mapping[str, Any]) -> ComposedOperator:
    if d.get("operator") is not None:
        return _parse_operator(d["operator"])
    prov = d.get("provenance") or ""
    if isinstance(prov, str) and prov[:1] in "[{":
        try:
            return _parse_operator(json.loads(prov))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    rel = str(d.get("relation") or d.get("kind") or "")
    args: dict[str, Any] = {}
    if isinstance(d.get("args"), Mapping):
        args.update(d["args"])
    if d.get("variable") not in (None, ""):
        args["variable"] = d["variable"]
    if d.get("target_value") not in (None, ""):
        args["target_value"] = d["target_value"]
    return _from_kind_args(rel, args)


def _parse_operator(obj: Any) -> ComposedOperator:
    if isinstance(obj, ComposedOperator):
        return obj
    if obj is None:
        return ComposedOperator(opaque=True, note="missing_operator")
    if isinstance(obj, LocalEdge):
        return _from_edge_dict(obj.to_dict())
    if isinstance(obj, (list, tuple)):
        if not obj:
            return ComposedOperator()
        return compose_operators(*obj)
    if isinstance(obj, str):
        kl = obj.strip().lower()
        if kl in {"identity", "id"}:
            return ComposedOperator()
        return ComposedOperator(
            tags=((obj, ()),),
            opaque=True,
            note="string_operator",
        )
    if isinstance(obj, Mapping):
        if _is_edge_mapping(obj):
            return _from_edge_dict(obj)
        kind = str(obj.get("kind") or obj.get("relation") or "")
        args = obj.get("args")
        if not isinstance(args, Mapping):
            skip = {
                "kind",
                "relation",
                "verdict",
                "provenance",
                "obligation_id",
                "operator",
                "member_id",
                "nodes",
                "edges",
            }
            args = {k: v for k, v in obj.items() if k not in skip}
        return _from_kind_args(kind, args)
    return ComposedOperator(opaque=True, note=f"unparsed:{type(obj).__name__}")


def _compose_maps(first: Mapping[str, str], second: Mapping[str, str]) -> dict[str, str]:
    """Apply ``first`` then ``second`` as one-step name maps."""
    names = set(first) | set(second) | set(first.values()) | set(second.values())
    out: dict[str, str] = {}
    for n in names:
        x = first.get(n, n)
        y = second.get(x, x)
        if y != n:
            out[n] = y
    return out


def _compose_pair(a: ComposedOperator, b: ComposedOperator) -> ComposedOperator:
    mapping = _compose_maps(a.as_map(), b.as_map())
    return ComposedOperator(
        mapping=tuple(sorted(mapping.items())),
        tags=a.tags + b.tags,
        opaque=a.opaque or b.opaque,
        note=b.note or a.note,
    )


def compose_operators(*parts: Any) -> ComposedOperator:
    """Compose operators left-to-right (first operator applies first)."""
    acc = ComposedOperator()
    if not parts:
        return acc
    for p in parts:
        acc = _compose_pair(acc, _parse_operator(p))
    return acc


def operators_agree(left: Any, right: Any) -> str:
    """ZERO if composed operators agree, NONZERO if maps conflict, else UNKNOWN."""
    a = left if isinstance(left, ComposedOperator) else compose_operators(left)
    b = right if isinstance(right, ComposedOperator) else compose_operators(right)
    ma, mb = a.as_map(), b.as_map()
    names = set(ma) | set(mb) | set(ma.values()) | set(mb.values())
    map_equal = all(ma.get(n, n) == mb.get(n, n) for n in names)
    if a.opaque or b.opaque:
        if a.opaque and b.opaque and map_equal and a.tags == b.tags:
            return ZERO
        return UNKNOWN
    a_tag_only = bool(a.tags) and not a.mapping
    b_tag_only = bool(b.tags) and not b.mapping
    if (a_tag_only and b.mapping and not b.tags) or (b_tag_only and a.mapping and not a.tags):
        return UNKNOWN
    if not map_equal:
        return NONZERO
    if a.tags == b.tags:
        return ZERO
    if not a.tags or not b.tags:
        return UNKNOWN
    kinds_a = tuple(t[0] for t in a.tags)
    kinds_b = tuple(t[0] for t in b.tags)
    if kinds_a == kinds_b:
        return NONZERO
    return UNKNOWN


def required_graph_connected(
    member_ids: Sequence[str],
    edges: Sequence[Any],
) -> bool:
    """Undirected connectivity of members under required edges."""
    ids = [str(m) for m in member_ids]
    uniq = list(dict.fromkeys(ids))
    if not uniq:
        return False
    if len(uniq) == 1:
        return True
    parent = {m: m for m in uniq}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for edge in edges:
        d = _edge_dict(edge)
        s, t = str(d.get("source") or ""), str(d.get("target") or "")
        if s in parent and t in parent:
            union(s, t)
    return len({find(m) for m in uniq}) == 1


def multiplicities_consistent(
    multiplicities: Mapping[str, Any] | Sequence[Any] | None,
) -> bool:
    """Positive integer claims; conflicting claims for one node fail."""
    if multiplicities is None:
        return True
    items: list[tuple[Any, Any]]
    if isinstance(multiplicities, Mapping):
        items = list(multiplicities.items())
    else:
        items = []
        for item in multiplicities:
            if isinstance(item, Mapping) and "node" in item and "multiplicity" in item:
                items.append((item["node"], item["multiplicity"]))
            elif isinstance(item, (tuple, list)) and len(item) == 2:
                items.append((item[0], item[1]))
            else:
                return False
    seen: dict[str, int] = {}
    for node, m in items:
        if type(m) is not int or isinstance(m, bool) or m < 1:
            return False
        key = str(node)
        if key in seen and seen[key] != m:
            return False
        seen[key] = m
    return True


def _nodes_of_path(path: Any, edges_used: Sequence[Any]) -> tuple[str, ...]:
    if isinstance(path, Mapping) and path.get("nodes"):
        return tuple(str(n) for n in path["nodes"])
    nodes: list[str] = []
    for edge in edges_used:
        if not isinstance(edge, (LocalEdge, Mapping)):
            continue
        d = _edge_dict(edge)
        s, t = str(d.get("source") or ""), str(d.get("target") or "")
        if not nodes:
            if s:
                nodes.append(s)
        if t:
            nodes.append(t)
    return tuple(nodes)


def _path_operator(path: Any) -> tuple[ComposedOperator, tuple[str, ...]]:
    if isinstance(path, Mapping):
        if path.get("operators") is not None:
            seq = list(path["operators"])
        elif path.get("edges") is not None:
            seq = list(path["edges"])
        else:
            seq = list(path.get("steps") or ())
        return compose_operators(*seq), _nodes_of_path(path, seq)
    seq = list(path)
    return compose_operators(*seq), _nodes_of_path({"edges": seq}, seq)


def _enumerate_simple_paths(
    members: Sequence[str],
    edges: Sequence[Any],
    max_path_length: int,
) -> tuple[list[tuple[tuple[str, ...], tuple[Any, ...]]], bool]:
    adj: dict[str, list[tuple[str, Any]]] = {}
    for edge in edges:
        d = _edge_dict(edge)
        s, t = str(d.get("source") or ""), str(d.get("target") or "")
        if not s or not t:
            continue
        adj.setdefault(s, []).append((t, edge))
    starts = [str(m) for m in members] if members else list(adj)
    found: list[tuple[tuple[str, ...], tuple[Any, ...]]] = []
    truncated = False

    def dfs(nodes: tuple[str, ...], used: tuple[Any, ...]) -> None:
        nonlocal truncated
        u = nodes[-1]
        hops = len(nodes) - 1
        if hops >= max_path_length:
            if any(v not in nodes for v, _e in adj.get(u, [])):
                truncated = True
            return
        for v, edge in adj.get(u, []):
            if v in nodes:
                continue
            nxt_nodes = nodes + (v,)
            nxt_used = used + (edge,)
            found.append((nxt_nodes, nxt_used))
            dfs(nxt_nodes, nxt_used)

    if max_path_length < 1:
        return [], True
    for s in starts:
        dfs((s,), ())
    return found, truncated


def path_consistency(
    edges: Sequence[Any] | None = None,
    *,
    members: Sequence[str] | None = None,
    paths: Sequence[Any] | None = None,
    max_path_length: int = 8,
) -> PathConsistencyResult:
    """Compare composed operators on distinct paths that share endpoints.

    Algebraic maps that differ are NONZERO. Opaque operators are UNKNOWN.
    At most one path between a pair is vacuously ZERO.
    """
    grouped: dict[tuple[str, str], list[tuple[tuple[str, ...], ComposedOperator]]] = {}
    truncated = False
    note = ""

    if paths is not None:
        raw: list[tuple[tuple[str, ...], ComposedOperator]] = []
        for path in paths:
            op, nodes = _path_operator(path)
            raw.append((nodes, op))
        if not raw:
            return PathConsistencyResult(UNKNOWN, note="no_paths")
        if all(n and len(n) >= 2 for n, _op in raw):
            for nodes, op in raw:
                grouped.setdefault((nodes[0], nodes[-1]), []).append((nodes, op))
        else:
            grouped[("*", "*")] = raw
    elif edges is not None:
        found, truncated = _enumerate_simple_paths(
            members or (),
            edges,
            max_path_length,
        )
        for nodes, used in found:
            op = compose_operators(*used)
            grouped.setdefault((nodes[0], nodes[-1]), []).append((nodes, op))
        if not edges:
            return PathConsistencyResult(UNKNOWN, truncated=truncated, note="no_edges")
        if not grouped:
            note = "no_directed_paths"
    else:
        return PathConsistencyResult(UNKNOWN, note="no_paths")

    verdicts: list[str] = []
    conflicts: list[PathConflict] = []
    for (src, dst), group in sorted(grouped.items()):
        if len(group) < 2:
            continue
        for (na, oa), (nb, ob) in combinations(group, 2):
            v = operators_agree(oa, ob)
            verdicts.append(v)
            if v != ZERO:
                conflicts.append(
                    PathConflict(
                        src=src,
                        dst=dst,
                        path_a=na,
                        path_b=nb,
                        verdict=v,
                        note="composed_operators_disagree"
                        if v == NONZERO
                        else "composed_operators_uncomparable",
                    )
                )
    combined = _combine_verdicts(verdicts)
    if truncated and combined == ZERO:
        combined = UNKNOWN
        note = note or "path_enumeration_truncated"
    if not verdicts and combined == ZERO:
        note = note or "vacuous_path_consistency"
        verdicts = [ZERO]
    return PathConsistencyResult(
        verdict=combined,
        path_verdicts=tuple(verdicts),
        conflicts=tuple(conflicts),
        truncated=truncated,
        note=note,
    )


def _recurrence_from(
    certificate: ConfluentFamilyCertificate | Mapping[str, Any] | None,
    override: Sequence[str] | None,
) -> list[str]:
    if override is not None:
        return [_normalize_verdict(v) for v in override]
    recs: Sequence[Any] = ()
    if isinstance(certificate, ConfluentFamilyCertificate):
        recs = certificate.recurrence_obligations
    elif isinstance(certificate, Mapping):
        recs = certificate.get("recurrence_obligations") or ()
    out: list[str] = []
    for item in recs:
        if isinstance(item, Mapping):
            out.append(_normalize_verdict(item.get("verdict")))
        elif isinstance(item, str):
            out.append(_normalize_verdict(item))
        else:
            out.append(UNKNOWN)
    return out


def _members_from(
    certificate: ConfluentFamilyCertificate | Mapping[str, Any] | None,
    member_ids: Sequence[str] | None,
    edges: Sequence[Any],
) -> list[str]:
    if member_ids is not None:
        return [str(m) for m in member_ids]
    if isinstance(certificate, ConfluentFamilyCertificate):
        return [str(m) for m in certificate.member_ids]
    if isinstance(certificate, Mapping) and certificate.get("member_ids"):
        return [str(m) for m in certificate["member_ids"]]
    ids: list[str] = []
    for edge in edges:
        d = _edge_dict(edge)
        for key in ("source", "target"):
            val = str(d.get(key) or "")
            if val and val not in ids:
                ids.append(val)
    return ids


def _edges_from(
    certificate: ConfluentFamilyCertificate | Mapping[str, Any] | None,
    edges: Sequence[Any] | None,
) -> list[Any]:
    if edges is not None:
        return list(edges)
    if isinstance(certificate, ConfluentFamilyCertificate):
        return list(certificate.local_edges)
    if isinstance(certificate, Mapping):
        return list(certificate.get("local_edges") or ())
    return []


def _multiplicities_from(
    certificate: ConfluentFamilyCertificate | Mapping[str, Any] | None,
    override: Mapping[str, Any] | Sequence[Any] | None,
) -> Mapping[str, Any] | Sequence[Any] | None:
    if override is not None:
        if isinstance(certificate, ConfluentFamilyCertificate) and certificate.node_multiplicities:
            claims: list[tuple[Any, Any]] = list(certificate.node_multiplicities.items())
            if isinstance(override, Mapping):
                claims.extend(override.items())
            else:
                claims.extend(
                    item if not isinstance(item, Mapping) else (item.get("node"), item.get("multiplicity"))
                    for item in override
                )
            return claims
        return override
    if isinstance(certificate, ConfluentFamilyCertificate):
        return certificate.node_multiplicities
    if isinstance(certificate, Mapping):
        return certificate.get("node_multiplicities") or {}
    return {}


def _latent_from(
    certificate: ConfluentFamilyCertificate | Mapping[str, Any] | None,
    override: bool | None,
) -> bool:
    if override is not None:
        return bool(override)
    if isinstance(certificate, Mapping) and "latent_compatible" in certificate:
        return bool(certificate["latent_compatible"])
    return True


def _to_local_edge(edge: Any) -> LocalEdge:
    if isinstance(edge, LocalEdge):
        return edge
    d = _edge_dict(edge)
    prov = d.get("provenance") or ""
    if d.get("operator") is not None and not prov:
        try:
            prov = json.dumps(d["operator"], sort_keys=True, default=str)
        except TypeError:
            prov = str(d["operator"])
    rel = str(d.get("relation") or d.get("kind") or "limit")
    return LocalEdge(
        source=str(d.get("source") or ""),
        target=str(d.get("target") or ""),
        relation=rel,
        variable=str(d.get("variable") or ""),
        target_value=str(d.get("target_value") or ""),
        obligation_id=str(d.get("obligation_id") or ""),
        verdict=_normalize_verdict(d.get("verdict")),
        provenance=str(prov),
    )


def _family_id(
    certificate: ConfluentFamilyCertificate | Mapping[str, Any] | None,
) -> str:
    if isinstance(certificate, ConfluentFamilyCertificate):
        return certificate.family_id
    if isinstance(certificate, Mapping):
        return str(certificate.get("family_id") or "")
    return ""


def certify_family(
    certificate: ConfluentFamilyCertificate | Mapping[str, Any] | None = None,
    *,
    member_ids: Sequence[str] | None = None,
    edges: Sequence[Any] | None = None,
    recurrence_verdicts: Sequence[str] | None = None,
    node_multiplicities: Mapping[str, Any] | Sequence[Any] | None = None,
    latent_compatible: bool | None = None,
    max_path_length: int = 8,
) -> FamilyCompositionResult:
    """Wrap ``compose_family_verdict`` with graph / path / multiplicity checks.

    Never counts ZERO edges. Pairwise ZERO is not FAMILY_ZERO.
    """
    edge_list = _edges_from(certificate, edges)
    ids = _members_from(certificate, member_ids, edge_list)
    rec = _recurrence_from(certificate, recurrence_verdicts)
    mult = _multiplicities_from(certificate, node_multiplicities)
    latent = _latent_from(certificate, latent_compatible)
    connected = required_graph_connected(ids, edge_list)
    mult_ok = multiplicities_consistent(mult)
    pc = path_consistency(
        edge_list,
        members=ids,
        max_path_length=max_path_length,
    )
    edge_verdicts = tuple(_normalize_verdict(_edge_dict(e).get("verdict")) for e in edge_list)
    rec_t = tuple(rec)
    if not edge_list:
        path_vs: tuple[str, ...] = ()
    else:
        path_vs = pc.path_verdicts if pc.path_verdicts else (pc.verdict,)

    family_verdict = compose_family_verdict(
        required_edge_verdicts=list(edge_verdicts),
        recurrence_verdicts=list(rec_t),
        path_verdicts=list(path_vs),
        connected=connected,
        multiplicities_consistent=mult_ok,
        latent_compatible=latent,
    )

    notes: list[str] = []
    if not ids:
        notes.append("empty_family")
    if not connected:
        notes.append("required_graph_disconnected")
    if not mult_ok:
        notes.append("multiplicities_inconsistent")
    if not latent:
        notes.append("latent_incompatible")
    if not edge_list:
        notes.append("no_required_edges")
    if pc.verdict != ZERO:
        notes.append(f"path_consistency:{pc.verdict}")
    if any(v == UNKNOWN for v in edge_verdicts):
        notes.append("required_edge_unknown")
    if any(v == NONZERO for v in edge_verdicts):
        notes.append("required_edge_nonzero")
    if any(v != ZERO for v in rec_t):
        notes.append("recurrence_not_zero")
    notes.append("no_majority")

    local_edges = [_to_local_edge(e) for e in edge_list]
    mult_dict: dict[str, int] = {}
    if isinstance(mult, Mapping):
        for k, v in mult.items():
            if type(v) is int and v >= 1:
                mult_dict[str(k)] = v
    consistency = [
        {
            "kind": "path_consistency",
            "verdict": pc.verdict,
            "note": pc.note,
            "n_conflicts": len(pc.conflicts),
        }
    ]
    if isinstance(certificate, ConfluentFamilyCertificate):
        cert = replace(
            certificate,
            member_ids=list(ids) if ids else list(certificate.member_ids),
            local_edges=local_edges or list(certificate.local_edges),
            node_multiplicities=mult_dict or dict(certificate.node_multiplicities),
            consistency_obligations=list(certificate.consistency_obligations) + consistency,
            family_verdict=family_verdict,
            provenance=list(certificate.provenance)
            + ["research.multibranch_verification.compose.certify_family"],
        )
    else:
        rec_obl: list[dict[str, Any]]
        if isinstance(certificate, Mapping):
            rec_obl = [dict(x) if isinstance(x, Mapping) else {"verdict": x} for x in (certificate.get("recurrence_obligations") or [])]
        else:
            rec_obl = [{"verdict": v} for v in rec_t]
        if rec_t and not rec_obl:
            rec_obl = [{"verdict": v} for v in rec_t]
        cert = ConfluentFamilyCertificate(
            family_id=_family_id(certificate),
            member_ids=list(ids),
            node_multiplicities=mult_dict,
            local_edges=local_edges,
            recurrence_obligations=rec_obl,
            consistency_obligations=consistency,
            family_verdict=family_verdict,
            provenance=["research.multibranch_verification.compose.certify_family"],
        )

    return FamilyCompositionResult(
        family_verdict=family_verdict,
        connected=connected,
        multiplicities_consistent=mult_ok,
        latent_compatible=latent,
        required_edge_verdicts=edge_verdicts,
        recurrence_verdicts=rec_t,
        path_verdicts=path_vs,
        path_consistency=pc,
        notes=tuple(notes),
        certificate=cert,
    )
