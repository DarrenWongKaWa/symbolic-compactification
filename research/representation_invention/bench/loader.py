"""ssc-representation-bench-v0.1 loader.

On-disk JSON keeps evaluation labels. proposer_view() is a whitelist
projection: hidden target labels never appear in the proposer payload.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Iterable, Optional

from research.representation_invention.ladder import R_LEVELS
from research.representation_invention.schema import GID_RE, REPRESENTATION_TYPES
from symbolic_compactification.models import HARD_RESERVED_NAMES, RESERVED_NAMES

VERSION = "ssc-representation-bench-v0.1"
TASK_NAME = "representation_invention"

BENCH_ROOT = Path(__file__).resolve().parent
TASKS_DEV = BENCH_ROOT / "tasks" / "dev"
TASKS_TEST = BENCH_ROOT / "tasks" / "test"
SCHEMA_PATH = BENCH_ROOT / "schema.json"
FREEZE_MANIFEST = BENCH_ROOT / "validation" / "freeze_manifest.json"

PUBLIC_FIELDS = (
    "id",
    "version",
    "tier",
    "family",
    "domain",
    "split",
    "task",
    "current",
    "source_expressions",
    "symbols",
    "functions",
    "assumptions",
    "catalog",
    "catalog_external",
    "scientific_context",
    "source_format",
    "license",
    "hidden_from_proposer",
)

CATALOG_PUBLIC_KEYS = ("id", "text", "kind")

HIDDEN_FIELDS = (
    "target_type",
    "hidden_target_type",
    "gold_types",
    "instance_maps",
    "hidden_instance_maps",
    "r_level",
    "hidden_r_level",
    "polarity",
    "negative_tempting_structures",
    "provenance_hidden",
    "provenance",
    "expected_verdict",
    "notes",
    "ladder_id",
    "difficulty",
    "human_reference",
    "target_compact",
    "hidden_gold",
    "gold_hypothesis_type",
    "gold_reconstruction",
    "gold_auxiliaries",
    "gold_members",
    "gold_latent",
    "gold_operator",
    "forbidden_types",
    "forbidden_reconstructions",
    "downstream_gold",
    "downstream",
)

REQUIRED_FIELDS = (
    "id",
    "version",
    "split",
    "tier",
    "family",
    "task",
    "current",
    "source_expressions",
    "symbols",
    "functions",
    "assumptions",
    "catalog",
    "source_format",
    "scientific_context",
    "hidden_from_proposer",
    "target_type",
    "instance_maps",
    "r_level",
    "polarity",
    "negative_tempting_structures",
    "provenance_hidden",
    "difficulty",
)

LEAK_STRINGS = (
    "Phi_Gamma",
    "phi_gamma",
    "PhiGamma",
    "φ_Γ",
    "hermite_divided_difference",
    "PRB master",
    "nine generator",
)

_R_LEVEL_RE = re.compile(r"\bR[0-8]\b")
_GOLD_RE = re.compile(r"\bgold", re.I)
_LADDER_L_RE = re.compile(r"\bL[4-7]\b")

_SPLIT_DIRS = {"dev": TASKS_DEV, "test": TASKS_TEST}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _task_paths(split: Optional[str] = None) -> list[Path]:
    if split is None:
        dirs: Iterable[Path] = (TASKS_DEV, TASKS_TEST)
    else:
        dirs = (_SPLIT_DIRS[split],)
    out: list[Path] = []
    for d in dirs:
        if d.is_dir():
            out.extend(sorted(d.glob("*.json")))
    return out


def load_split(split: str) -> list[dict]:
    items = [load_json(p) for p in _task_paths(split)]
    for it in items:
        validate_task(it, expected_split=split)
    return items


def load_dev() -> list[dict]:
    return load_split("dev")


def load_test() -> list[dict]:
    return load_split("test")


def load_all() -> list[dict]:
    return load_dev() + load_test()


def _strip_catalog(raw: Any) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        out.append({k: entry[k] for k in CATALOG_PUBLIC_KEYS if k in entry})
    return out


def proposer_view(item: dict) -> dict:
    """Whitelist projection. Hidden evaluation labels are dropped."""
    view: dict[str, Any] = {}
    for key in PUBLIC_FIELDS:
        if key not in item:
            continue
        if key == "catalog":
            view[key] = _strip_catalog(item[key])
        else:
            view[key] = copy.deepcopy(item[key])
    view["hidden_from_proposer"] = True
    return view


def _blob(payload: Any) -> str:
    return json.dumps(payload, default=str)


def leakage_hits(payload: Any, extra_forbidden: tuple[str, ...] = ()) -> list[str]:
    blob = _blob(payload)
    hits: list[str] = []
    for key in HIDDEN_FIELDS + extra_forbidden:
        token = f'"{key}"'
        if token in blob:
            hits.append(key)
    for tok in LEAK_STRINGS:
        if tok and tok in blob:
            hits.append(tok)
    if _R_LEVEL_RE.search(blob):
        hits.append("R-level")
    if _GOLD_RE.search(blob):
        hits.append("gold")
    if _LADDER_L_RE.search(blob):
        hits.append("L4-L7")
    return hits


def assert_no_leakage(payload: Any, extra_forbidden: tuple[str, ...] = ()) -> None:
    hits = leakage_hits(payload, extra_forbidden)
    if hits:
        raise RuntimeError(f"F_LEAK: hidden material in proposer payload: {hits}")


def _require(item: dict, key: str) -> None:
    if key not in item:
        raise ValueError(f"{item.get('id', '<unknown>')}: missing field {key}")


def validate_task(item: dict, *, expected_split: Optional[str] = None) -> None:
    tid = str(item.get("id") or "<unknown>")
    if not isinstance(item, dict):
        raise ValueError("task is not an object")
    for key in REQUIRED_FIELDS:
        _require(item, key)

    if item.get("version") != VERSION:
        raise ValueError(f"{tid}: version must be {VERSION}")
    if item.get("task") != TASK_NAME:
        raise ValueError(f"{tid}: task must be {TASK_NAME}")
    split = item.get("split")
    if split not in ("dev", "test"):
        raise ValueError(f"{tid}: bad split")
    if expected_split is not None and split != expected_split:
        raise ValueError(f"{tid}: split {split} != {expected_split}")
    if item.get("tier") not in ("A", "B", "C"):
        raise ValueError(f"{tid}: bad tier")
    if item.get("source_format") != "sympy":
        raise ValueError(f"{tid}: source_format must be sympy")
    if item.get("hidden_from_proposer") is not True:
        raise ValueError(f"{tid}: hidden_from_proposer must be true")
    if item.get("polarity") not in ("positive", "negative"):
        raise ValueError(f"{tid}: bad polarity")

    external = bool(item.get("catalog_external"))
    if external and split != "dev":
        raise ValueError(f"{tid}: external catalog is DEV-only")

    current = item.get("current")
    if not isinstance(current, str):
        raise ValueError(f"{tid}: current must be a string")
    if not current.strip() and not external:
        raise ValueError(f"{tid}: empty current")

    src = item.get("source_expressions")
    if not isinstance(src, list) or not all(isinstance(s, str) for s in src):
        raise ValueError(f"{tid}: source_expressions must be a string list")
    if not src and not external:
        raise ValueError(f"{tid}: source_expressions empty")

    for key in ("functions", "assumptions", "scientific_context"):
        val = item.get(key)
        if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
            raise ValueError(f"{tid}: {key} must be a string list")

    symbols = item.get("symbols")
    if not isinstance(symbols, list):
        raise ValueError(f"{tid}: symbols must be a list")
    names: list[str] = []
    for s in symbols:
        if not isinstance(s, dict) or not s.get("name"):
            raise ValueError(f"{tid}: symbol missing name")
        names.append(str(s["name"]))
    if len(names) != len(set(names)):
        raise ValueError(f"{tid}: duplicate symbol names")
    reserved = set(names) & set(RESERVED_NAMES)
    if reserved:
        raise ValueError(f"{tid}: reserved symbol names {sorted(reserved)}")
    hard_fn = set(item.get("functions") or []) & set(HARD_RESERVED_NAMES)
    if hard_fn:
        raise ValueError(f"{tid}: reserved function names {sorted(hard_fn)}")

    catalog = item.get("catalog")
    if not isinstance(catalog, list):
        raise ValueError(f"{tid}: catalog must be a list")
    if not catalog and not external:
        raise ValueError(f"{tid}: catalog empty")
    seen: set[str] = set()
    for entry in catalog:
        if not isinstance(entry, dict):
            raise ValueError(f"{tid}: catalog entry not an object")
        gid = str(entry.get("id") or "")
        text = entry.get("text")
        if not GID_RE.fullmatch(gid):
            raise ValueError(f"{tid}: catalog id not G####: {gid}")
        if gid in seen:
            raise ValueError(f"{tid}: duplicate catalog id {gid}")
        seen.add(gid)
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{tid}: catalog {gid} missing text")

    ttype = item.get("target_type")
    if ttype is not None and ttype not in REPRESENTATION_TYPES:
        raise ValueError(f"{tid}: unknown target_type {ttype}")
    rlv = item.get("r_level")
    if rlv is not None and rlv not in R_LEVELS:
        raise ValueError(f"{tid}: bad r_level {rlv}")
    if item.get("polarity") == "negative":
        if ttype is not None:
            raise ValueError(f"{tid}: negative task must not name a target_type")
    else:
        if ttype is None and not external:
            raise ValueError(f"{tid}: positive task missing target_type")

    imap = item.get("instance_maps")
    if not isinstance(imap, dict):
        raise ValueError(f"{tid}: instance_maps must be an object")
    for k in imap:
        ks = str(k)
        if GID_RE.fullmatch(ks) and ks not in seen and not external:
            raise ValueError(f"{tid}: instance_maps id not in catalog: {ks}")

    nts = item.get("negative_tempting_structures")
    if not isinstance(nts, list) or not all(isinstance(x, str) for x in nts):
        raise ValueError(f"{tid}: negative_tempting_structures must be a string list")
    if item.get("polarity") == "negative" and not nts:
        raise ValueError(f"{tid}: negative task needs tempting structures")

    diff = item.get("difficulty")
    if not isinstance(diff, int) or isinstance(diff, bool) or not 1 <= diff <= 5:
        raise ValueError(f"{tid}: difficulty must be int 1..5")

    if split == "test":
        blob = _blob(item).lower()
        if "guo" in blob or "sigma_abc" in blob or "phi_gamma" in blob:
            raise ValueError(f"{tid}: TEST must not contain Guo material")
