"""One-parameter confluence paths between existing family members.

Evaluation-only. Connects G#### members already in the frozen family.
Does not invent intermediate branches, does not join incomparable
diagonals, and does not emit V2 two-parameter star edges as paths.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from research.iterated_confluence.schema import (
    PATH_UNKNOWN,
    UNKNOWN,
    PathCertificate,
    PathStep,
)
from research.multibranch_verification.graph.build import (
    _PREFERRED_DIR,
    _is_true,
    _parse_equalities,
)
from research.multibranch_verification.piecewise import (
    UNKNOWN_ROLE,
    classify_condition,
)

HERE = Path(__file__).resolve().parent
FROZEN_PATH = HERE.parent / "FROZEN_INPUTS_V3.json"
OUT = HERE / "PATH_CANDIDATES.json"

ONE_PARAMETER = "one_parameter_confluence"
REPEATED_NODE = "repeated_node_confluence"
SUBSTITUTION = "substitution"

# Preferred remaining equalities: (m,n), then (ell,n), then (ell,m).
# After Eq(ell, m) the remaining free coordinate that reaches And is Eq(m, n).
PREFERRED_PAIRS: tuple[tuple[str, str], ...] = tuple(
    _PREFERRED_DIR[key]
    for key in (
        frozenset({"m", "n"}),
        frozenset({"ell", "n"}),
        frozenset({"ell", "m"}),
    )
)

_EPS_NAME = re.compile(r"epsilon\(([A-Za-z]+)\)")


class _UF:
    """Union-find over declared index names."""

    def __init__(self, names: Sequence[str], eqs: Sequence[tuple[str, str]]) -> None:
        self.parent = {n: n for n in names}
        self.rank = {n: 0 for n in names}
        for a, b in eqs:
            self.union(a, b)

    def find(self, x: str) -> str:
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(self, a: str, b: str) -> bool:
        if a not in self.parent or b not in self.parent:
            return False
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1
        return True

    def same(self, a: str, b: str) -> bool:
        if a not in self.parent or b not in self.parent:
            return False
        return self.find(a) == self.find(b)

    def blocks(self) -> frozenset[frozenset[str]]:
        groups: dict[str, set[str]] = {}
        for n in self.parent:
            groups.setdefault(self.find(n), set()).add(n)
        return frozenset(frozenset(g) for g in groups.values())


def _eps(name: str) -> str:
    return f"epsilon({name})"


def _directed(a: str, b: str) -> tuple[str, str]:
    pref = _PREFERRED_DIR.get(frozenset({a, b}))
    if pref:
        return pref
    return (a, b) if a <= b else (b, a)


def _is_coarsening(
    names: Sequence[str],
    src_eqs: Sequence[tuple[str, str]],
    tgt_eqs: Sequence[tuple[str, str]],
) -> bool:
    src = _UF(names, src_eqs)
    tgt = _UF(names, tgt_eqs)
    for n in names:
        for m in names:
            if src.same(n, m) and not tgt.same(n, m):
                return False
    return True


def _n_params(
    names: Sequence[str],
    src_eqs: Sequence[tuple[str, str]],
    tgt_eqs: Sequence[tuple[str, str]],
) -> int:
    return len(_UF(names, src_eqs).blocks()) - len(_UF(names, tgt_eqs).blocks())


def _step_coordinate(
    names: Sequence[str],
    src_eqs: Sequence[tuple[str, str]],
    tgt_eqs: Sequence[tuple[str, str]],
) -> tuple[str, str]:
    src = _UF(names, src_eqs)
    tgt = _UF(names, tgt_eqs)
    for a, b in PREFERRED_PAIRS:
        if a in src.parent and b in src.parent:
            if (not src.same(a, b)) and tgt.same(a, b):
                return a, b
    candidates: list[tuple[str, str]] = []
    name_list = list(names)
    for i, a in enumerate(name_list):
        for b in name_list[i + 1 :]:
            if (not src.same(a, b)) and tgt.same(a, b):
                candidates.append(_directed(a, b))
    if not candidates:
        raise ValueError("one-parameter step without a merge coordinate")
    candidates.sort()
    return candidates[0]


def _multi_coordinates(
    names: Sequence[str],
    src_eqs: Sequence[tuple[str, str]],
    tgt_eqs: Sequence[tuple[str, str]],
) -> list[tuple[str, str]]:
    src = _UF(names, src_eqs)
    tgt = _UF(names, tgt_eqs)
    coords: list[tuple[str, str]] = []
    for a, b in PREFERRED_PAIRS:
        if a not in src.parent or b not in src.parent:
            continue
        if (not src.same(a, b)) and tgt.same(a, b):
            coords.append((a, b))
            src.union(a, b)
    if len(src.blocks()) != len(tgt.blocks()):
        name_list = list(names)
        for i, a in enumerate(name_list):
            for b in name_list[i + 1 :]:
                if (not src.same(a, b)) and tgt.same(a, b):
                    pair = _directed(a, b)
                    coords.append(pair)
                    src.union(pair[0], pair[1])
    coords.sort(key=lambda p: (_eps(p[0]), _eps(p[1])))
    return coords


def _index_universe(hyp: dict[str, Any], eqs_by_member: Iterable[Sequence[tuple[str, str]]]) -> list[str]:
    seen: set[str] = set()
    for eqs in eqs_by_member:
        for a, b in eqs:
            seen.add(a)
            seen.add(b)
    for tok in hyp.get("degeneracy_variables") or []:
        m = _EPS_NAME.fullmatch(str(tok).strip())
        if m:
            seen.add(m.group(1))
    return sorted(seen)


def _op_count(hyp: dict[str, Any], member_id: str) -> int:
    counts = hyp.get("op_counts") or {}
    val = counts.get(member_id)
    if isinstance(val, int):
        return val
    for rec in hyp.get("members") or []:
        if str(rec.get("member_id") or "") == member_id:
            ops = rec.get("ops")
            if isinstance(ops, int):
                return ops
    return 0


def _member_records(hyp: dict[str, Any]) -> list[dict[str, Any]]:
    branch = hyp.get("branch_conditions") or {}
    out: list[dict[str, Any]] = []
    for rec in hyp.get("members") or []:
        mid = str(rec.get("member_id") or "")
        if not mid:
            continue
        cond = rec.get("cond")
        if cond is None or str(cond).strip() == "":
            cond = branch.get(mid, "")
        cond_s = "True" if cond is True else str(cond)
        eqs = _parse_equalities(cond_s)
        info = classify_condition(cond_s)
        role = str(info.get("role") or UNKNOWN_ROLE)
        out.append(
            {
                "member_id": mid,
                "cond": cond_s,
                "eqs": eqs,
                "role": role,
                "parent_gid": str(rec.get("parent_gid") or ""),
                "ops": _op_count(hyp, mid),
            }
        )
    return out


def _covering_and_rejected(
    family_id: str,
    names: Sequence[str],
    records: Sequence[dict[str, Any]],
) -> tuple[list[PathStep], list[dict[str, Any]]]:
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        if rec["role"] == UNKNOWN_ROLE and not _is_true(rec["cond"]):
            continue
        by_parent[rec["parent_gid"]].append(rec)

    edges: list[PathStep] = []
    rejected: list[dict[str, Any]] = []
    seen_edge: set[tuple[str, str]] = set()
    seen_rej: set[tuple[str, str]] = set()
    if not names:
        return edges, rejected

    for group in by_parent.values():
        for src in group:
            for tgt in group:
                if src["member_id"] == tgt["member_id"]:
                    continue
                if not _is_coarsening(names, src["eqs"], tgt["eqs"]):
                    continue
                npar = _n_params(names, src["eqs"], tgt["eqs"])
                key = (src["member_id"], tgt["member_id"])
                if npar == 1:
                    if key in seen_edge:
                        continue
                    seen_edge.add(key)
                    a, b = _step_coordinate(names, src["eqs"], tgt["eqs"])
                    edges.append(
                        PathStep(
                            source=src["member_id"],
                            target=tgt["member_id"],
                            variable=_eps(a),
                            target_value=_eps(b),
                            relation=ONE_PARAMETER,
                            verdict=UNKNOWN,
                            provenance="cond",
                            obligation_id=(
                                f"{family_id}:{src['member_id']}->"
                                f"{tgt['member_id']}:{ONE_PARAMETER}"
                            ),
                        )
                    )
                elif npar >= 2:
                    if key in seen_rej:
                        continue
                    seen_rej.add(key)
                    coords = _multi_coordinates(names, src["eqs"], tgt["eqs"])
                    rejected.append(
                        {
                            "source": src["member_id"],
                            "target": tgt["member_id"],
                            "relation": REPEATED_NODE,
                            "variable": ",".join(_eps(a) for a, _ in coords),
                            "target_value": ",".join(_eps(b) for _, b in coords),
                            "reason": "not_one_parameter",
                            "n_parameters": npar,
                        }
                    )
    edges.sort(key=lambda e: (e.source, e.target, e.variable, e.target_value))
    rejected.sort(key=lambda r: (r["source"], r["target"]))
    return edges, rejected


def _compose_paths(
    family_id: str,
    edges: Sequence[PathStep],
    member_ids: Sequence[str],
) -> list[PathCertificate]:
    adj: dict[str, list[PathStep]] = defaultdict(list)
    for e in edges:
        adj[e.source].append(e)
    for src in adj:
        adj[src].sort(key=lambda e: (e.target, e.variable, e.target_value))

    out: list[PathCertificate] = []

    def dfs(node: str, steps: list[PathStep], seen: set[str]) -> None:
        if steps:
            chain = [steps[0].source, *[s.target for s in steps]]
            out.append(
                PathCertificate(
                    path_id=f"{family_id}:{'->'.join(chain)}",
                    start_member=chain[0],
                    end_member=chain[-1],
                    steps=list(steps),
                    path_verdict=PATH_UNKNOWN,
                    provenance=["existing_members_only", "one_parameter_covering"],
                )
            )
        for e in adj.get(node, []):
            if e.target in seen:
                continue
            dfs(e.target, steps + [e], seen | {e.target})

    for start in member_ids:
        dfs(start, [], {start})
    return out


def _is_certified_shape(path: PathCertificate, by_id: dict[str, dict[str, Any]]) -> bool:
    """True -> Eq(m, n) one-step, same shape as Track V two-member pairs."""
    if len(path.steps) != 1:
        return False
    src = by_id.get(path.start_member)
    tgt = by_id.get(path.end_member)
    if src is None or tgt is None:
        return False
    if not _is_true(src["cond"]):
        return False
    eqs = tgt["eqs"]
    return len(eqs) == 1 and set(eqs[0]) == {"m", "n"}


def _max_ops(path: PathCertificate, by_id: dict[str, dict[str, Any]]) -> int:
    m = 0
    for step in path.steps:
        for mid in (step.source, step.target):
            rec = by_id.get(mid) or {}
            ops = rec.get("ops") or 0
            if isinstance(ops, int) and ops > m:
                m = ops
    return m


def _rank_key(
    path: PathCertificate,
    by_id: dict[str, dict[str, Any]],
) -> tuple[int, int, int, str]:
    certified = 0 if _is_certified_shape(path, by_id) else 1
    return (len(path.steps), _max_ops(path, by_id), certified, path.path_id)


def _substitutions(hyp: dict[str, Any], member_ids: set[str]) -> list[dict[str, Any]]:
    operators = [o for o in (hyp.get("operators") or []) if isinstance(o, dict)]
    identity = ""
    for op in operators:
        if str(op.get("kind") or "") == "identity":
            identity = str(op.get("member_id") or op.get("member") or "")
            break
    out: list[dict[str, Any]] = []
    for op in operators:
        if str(op.get("kind") or "") != SUBSTITUTION:
            continue
        tgt = str(op.get("member_id") or op.get("member") or "")
        if tgt not in member_ids:
            continue
        src = identity
        if not src or src == tgt or src not in member_ids:
            generics = [
                str(m.get("member_id") or "")
                for m in (hyp.get("members") or [])
                if _is_true(str(m.get("cond") or ""))
            ]
            src = next((g for g in generics if g and g != tgt), "")
        if not src or src == tgt:
            continue
        args = op.get("args") if isinstance(op.get("args"), dict) else {}
        blob = args.get("substitution") if isinstance(args.get("substitution"), dict) else args
        variable = ""
        target_value = ""
        items = []
        for k, v in (blob or {}).items():
            if isinstance(v, (str, int)):
                items.append((str(k), str(v)))
        for a, b in sorted(items):
            if a != b:
                variable, target_value = a, b
                break
        out.append(
            PathStep(
                source=src,
                target=tgt,
                variable=variable,
                target_value=target_value,
                relation=SUBSTITUTION,
                verdict=UNKNOWN,
                provenance="operator:substitution",
            ).to_dict()
        )
    out.sort(key=lambda r: (r["source"], r["target"], r["variable"]))
    return out


def enumerate_family(hyp: dict[str, Any]) -> dict[str, Any]:
    """Enumerate one-parameter covering paths for one frozen hypothesis."""
    family_id = str(hyp.get("family_id") or "")
    member_ids = [str(x) for x in (hyp.get("member_ids") or [])]
    member_set = set(member_ids)
    records = [r for r in _member_records(hyp) if r["member_id"] in member_set]
    by_id = {r["member_id"]: r for r in records}
    names = _index_universe(hyp, (r["eqs"] for r in records))
    edges, rejected = _covering_and_rejected(family_id, names, records)
    paths = _compose_paths(family_id, edges, member_ids)
    paths.sort(key=lambda p: _rank_key(p, by_id))
    return {
        "family_id": family_id,
        "member_ids": list(member_ids),
        "paths": [p.to_dict() for p in paths],
        "rejected_multi_parameter": rejected,
        "substitutions": _substitutions(hyp, member_set),
    }


def _load_frozen(path: Optional[Path] = None) -> dict[str, Any]:
    return json.loads((path or FROZEN_PATH).read_text(encoding="utf-8"))


def enumerate_all(frozen: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    frozen = frozen or _load_frozen()
    families = [
        enumerate_family(hyp)
        for hyp in (frozen.get("hypotheses") or [])
        if isinstance(hyp, dict)
    ]
    return {
        "track": "V3",
        "agent": "V3-B",
        "evaluation_only": True,
        "does_not_adjudicate": True,
        "no_llm_calls": True,
        "source_frozen": "research/iterated_confluence/FROZEN_INPUTS_V3.json",
        "n_families": len(families),
        "family_ids": [f["family_id"] for f in families],
        "ranking": [
            "n_steps_ascending",
            "max_source_target_ops_ascending",
            "certified_true_eq_mn_shape",
            "path_id_lexicographic",
        ],
        "families": families,
    }


def dumps(blob: dict[str, Any]) -> str:
    return json.dumps(blob, indent=2, ensure_ascii=True) + "\n"


def write(path: Optional[Path] = None) -> Path:
    dest = path or OUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = dumps(enumerate_all())
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(dest)
    return dest


def load(path: Optional[Path] = None) -> dict[str, Any]:
    return json.loads((path or OUT).read_text(encoding="utf-8"))


def main() -> None:
    dest = write()
    blob = json.loads(dest.read_text(encoding="utf-8"))
    print("wrote", dest, "n_families", blob.get("n_families"))


if __name__ == "__main__":
    main()
