"""Degeneracy coordinates implied by piecewise conditions and operators.

Coordinates are undirected index equalities already present in branch
conditions or hypothesis operators. Substitution is recorded separately
and is not a degeneracy coordinate. Does not infer a representation and
does not emit a family verdict.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Optional

from research.multibranch_verification.graph.build import (
    _as_eps,
    _EPS_RE,
    _limit_ops,
    _pairs_from_args,
    _parse_equalities,
    _substitution_map,
    _xyz_map,
)
from research.multibranch_verification.piecewise import classify_condition

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
FROZEN_PATH = HERE.parent / "FROZEN_INPUTS_V3.json"
OUT = HERE / "DEGENERACY_COORDINATES.json"

_INDEX_NAMES = frozenset({"ell", "m", "n"})
_PAIR_ID_RE = re.compile(r"^\{([^,]+),([^,]+)\}$")

# (ell=m) follows from (ell=n and m=n). Not a new representation.
LINEAR_DEPENDENCE_NOTE = (
    "(ell=m) follows from (ell=n and m=n). "
    "The three pairwise equalities are linearly dependent; "
    "dependence is not a new representation."
)
SUBSTITUTION_NOTE = "substitution is not a degeneracy coordinate"


def _pair_id(a: str, b: str) -> str:
    x, y = (a, b) if a <= b else (b, a)
    return "{" + x + "," + y + "}"


def _split_pair_id(pid: str) -> tuple[str, str]:
    m = _PAIR_ID_RE.match(pid)
    if m:
        return m.group(1), m.group(2)
    inner = pid.strip()
    if inner.startswith("{") and inner.endswith("}"):
        inner = inner[1:-1]
    a, b = inner.split(",", 1)
    return a.strip(), b.strip()


def _epsilon_form(a: str, b: str) -> str:
    x, y = (a, b) if a <= b else (b, a)
    return f"epsilon({x})-epsilon({y})"


def _index_from_token(token: str, xyz: dict[str, str]) -> Optional[str]:
    raw = (token or "").strip()
    if not raw:
        return None
    if raw in _INDEX_NAMES:
        return raw
    eps = _as_eps(raw, xyz)
    m = _EPS_RE.search(eps)
    if not m:
        return None
    name = m.group(1)
    if name in _INDEX_NAMES:
        return name
    return None


def _known_indices(hyp: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for rec in hyp.get("members") or []:
        if not isinstance(rec, dict):
            continue
        for a, b in _parse_equalities(str(rec.get("cond") or "")):
            names.add(a)
            names.add(b)
    for cond in (hyp.get("branch_conditions") or {}).values():
        for a, b in _parse_equalities(str(cond or "")):
            names.add(a)
            names.add(b)
    for var in hyp.get("degeneracy_variables") or []:
        m = _EPS_RE.search(str(var))
        if m:
            names.add(m.group(1))
    return names


def _accept_index(name: Optional[str], known: set[str]) -> bool:
    if not name:
        return False
    if known:
        return name in known
    return name in _INDEX_NAMES


def _union_find(pairs: list[tuple[str, str]]) -> Callable[[str], str]:
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    return find


def _member_map(hyp: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rec in hyp.get("members") or []:
        if not isinstance(rec, dict):
            continue
        mid = str(rec.get("member_id") or rec.get("member") or "")
        if mid:
            out[mid] = rec
    return out


def _member_ids(hyp: dict[str, Any]) -> list[str]:
    raw = hyp.get("member_ids")
    if isinstance(raw, list) and raw:
        return [str(x) for x in raw]
    return [str(m.get("member_id") or "") for m in (hyp.get("members") or []) if m]


def _cond_of(
    mid: str,
    by_id: dict[str, dict[str, Any]],
    branch_conditions: dict[str, Any],
) -> str:
    rec = by_id.get(mid) or {}
    if rec.get("cond") is not None:
        return str(rec.get("cond"))
    if mid in branch_conditions:
        return str(branch_conditions.get(mid) or "")
    return ""


def _active_from_cond(cond: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for a, b in _parse_equalities(cond):
        if a == b:
            continue
        pid = _pair_id(a, b)
        if pid not in seen:
            seen.add(pid)
            out.append(pid)
    out.sort()
    return out


def _free_coordinates(family_coords: list[str], active: list[str]) -> list[str]:
    find = _union_find([_split_pair_id(p) for p in active])
    free: list[str] = []
    for pid in family_coords:
        a, b = _split_pair_id(pid)
        if find(a) != find(b):
            free.append(pid)
    return free


def _pairs_from_limit_args(
    args: dict[str, Any],
    xyz: dict[str, str],
    known: set[str],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for src, tgt in _pairs_from_args(args, xyz):
        ia = _index_from_token(src, xyz)
        ib = _index_from_token(tgt, xyz)
        if not _accept_index(ia, known) or not _accept_index(ib, known):
            continue
        if ia == ib:
            continue
        pid = _pair_id(ia, ib)
        if pid in seen:
            continue
        seen.add(pid)
        pairs.append((ia, ib))
    return pairs


def _family_coordinates(
    hyp: dict[str, Any],
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    """Observed undirected equalities and operator epsilon presentations."""
    xyz = _xyz_map(str(hyp.get("reconstruction_rule") or ""))
    known = _known_indices(hyp)
    sources: dict[str, list[str]] = {}
    eps_forms: list[str] = []
    eps_seen: set[str] = set()

    def add(pid: str, source: str) -> None:
        bucket = sources.setdefault(pid, [])
        if source not in bucket:
            bucket.append(source)

    by_id = _member_map(hyp)
    branch_conditions = hyp.get("branch_conditions") or {}
    for mid in _member_ids(hyp):
        cond = _cond_of(mid, by_id, branch_conditions)
        for a, b in _parse_equalities(cond):
            if a == b:
                continue
            if not _accept_index(a, known) or not _accept_index(b, known):
                continue
            add(_pair_id(a, b), "cond")

    operators = [o for o in (hyp.get("operators") or []) if isinstance(o, dict)]
    for op in _limit_ops(operators):
        args = op.get("args") if isinstance(op.get("args"), dict) else {}
        for a, b in _pairs_from_limit_args(args, xyz, known):
            pid = _pair_id(a, b)
            add(pid, "operator")
            form = _epsilon_form(a, b)
            if form not in eps_seen:
                eps_seen.add(form)
                eps_forms.append(form)

    coords = sorted(sources)
    eps_forms.sort()
    return coords, eps_forms, sources


def _linear_dependence(coords: list[str]) -> Optional[dict[str, Any]]:
    needed = {"{ell,m}", "{ell,n}", "{m,n}"}
    if not needed.issubset(set(coords)):
        return None
    return {
        "note": LINEAR_DEPENDENCE_NOTE,
        "implied": "{ell,m}",
        "by": ["{ell,n}", "{m,n}"],
    }


def _one_substitution(
    member_id: str,
    args: dict[str, Any],
    *,
    nested_under: str = "",
) -> Optional[dict[str, Any]]:
    mapping = _substitution_map(args)
    if not mapping:
        return None
    rec: dict[str, Any] = {
        "member_id": member_id,
        "kind": "substitution",
        "map": dict(sorted(mapping.items())),
        "note": SUBSTITUTION_NOTE,
    }
    if nested_under:
        rec["nested_under"] = nested_under
    return rec


def _substitution_operators(hyp: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for op in hyp.get("operators") or []:
        if not isinstance(op, dict):
            continue
        mid = str(op.get("member_id") or op.get("member") or "")
        kind = str(op.get("kind") or "")
        args = op.get("args") if isinstance(op.get("args"), dict) else {}
        if kind == "substitution":
            rec = _one_substitution(mid, args)
            if rec:
                out.append(rec)
            continue
        compose = args.get("compose") if kind == "other" else None
        if not isinstance(compose, list):
            continue
        for step in compose:
            if not isinstance(step, dict):
                continue
            if str(step.get("kind") or "") != "substitution":
                continue
            step_args = step.get("args") if isinstance(step.get("args"), dict) else {}
            rec = _one_substitution(mid, step_args, nested_under="other")
            if rec:
                out.append(rec)
    return out


def analyze_family(hyp: dict[str, Any]) -> dict[str, Any]:
    """Coordinates and per-member active/free table for one frozen family."""
    family_id = str(hyp.get("family_id") or "")
    member_ids = _member_ids(hyp)
    by_id = _member_map(hyp)
    branch_conditions = hyp.get("branch_conditions") or {}
    coords, eps_forms, sources = _family_coordinates(hyp)
    members: list[dict[str, Any]] = []
    for mid in member_ids:
        cond = _cond_of(mid, by_id, branch_conditions)
        role = classify_condition(cond)["role"]
        active = _active_from_cond(cond)
        members.append(
            {
                "member_id": mid,
                "cond": cond,
                "role": role,
                "active_equalities": active,
                "free_coordinates": _free_coordinates(coords, active),
            }
        )
    payload: dict[str, Any] = {
        "family_id": family_id,
        "coordinates": coords,
        "operator_epsilon_pairs": eps_forms,
        "coordinate_sources": {k: list(sources[k]) for k in coords},
        "linear_dependence": _linear_dependence(coords),
        "substitution_operators": _substitution_operators(hyp),
        "members": members,
    }
    return payload


def analyze_all(frozen: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Tables for every family in FROZEN_INPUTS_V3.json."""
    blob = frozen if frozen is not None else json.loads(
        FROZEN_PATH.read_text(encoding="utf-8")
    )
    hyps = [h for h in (blob.get("hypotheses") or []) if isinstance(h, dict)]
    families = [analyze_family(h) for h in hyps]
    return {
        "track": "V3",
        "agent": "V3-A",
        "evaluation_only": True,
        "does_not_adjudicate": True,
        "no_llm_calls": True,
        "source_frozen": "research/iterated_confluence/FROZEN_INPUTS_V3.json",
        "n_families": len(families),
        "linear_dependence_note": LINEAR_DEPENDENCE_NOTE,
        "families": families,
    }


def dumps(blob: dict[str, Any]) -> str:
    return json.dumps(blob, indent=2, ensure_ascii=True) + "\n"


def write(path: Optional[Path] = None) -> Path:
    dest = path or OUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = dumps(analyze_all())
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
