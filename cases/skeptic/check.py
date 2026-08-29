"""Reject miner dossiers that fail the assumption-complete admission skeptic."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from research.assumption_complete_representation.schema import NOT_DECLARED

TRIVIAL_CSE = "TRIVIAL_CSE"
OBVIOUS_LGG = "OBVIOUS_LGG"
TARGET_LEAKED_BY_NOTATION = "TARGET_LEAKED_BY_NOTATION"
UNVERIFIABLE = "UNVERIFIABLE"
UNDER_SPECIFIED = "UNDER_SPECIFIED"
SYNTHETIC_DISGUISED_AS_SCIENTIFIC = "SYNTHETIC_DISGUISED_AS_SCIENTIFIC"
SELECTED_BECAUSE_METHOD_WORKS = "SELECTED_BECAUSE_METHOD_WORKS"
GUO_RESCUE = "GUO_RESCUE"
SILENT_PHYSICS_POSITIVITY = "SILENT_PHYSICS_POSITIVITY"

REASON_CODES = (
    TRIVIAL_CSE,
    OBVIOUS_LGG,
    TARGET_LEAKED_BY_NOTATION,
    UNVERIFIABLE,
    UNDER_SPECIFIED,
    SYNTHETIC_DISGUISED_AS_SCIENTIFIC,
    SELECTED_BECAUSE_METHOD_WORKS,
    GUO_RESCUE,
    SILENT_PHYSICS_POSITIVITY,
)

LEAKED_WORDS = (
    "hermite-on-guo",
    "phi_gamma",
    "the master function is",
)

_LGG_NEEDLES = (
    "least general generalization",
    "least-general generalization",
    "obvious lgg",
    "frozen lgg",
)

_SYNTHETIC_DOMAINS = {
    "synthetic",
    "toy",
    "generated",
    "author-constructed",
    "author_constructed",
}

_METHOD_WORKS_NEEDLES = (
    "already works",
    "method already",
    "known success of the method",
    "selected because the method",
    "we already compactified",
)

_PHYSICS_POS_RE = re.compile(
    r"(?:\bT\b|\bbeta\b|\bgamma\b|\bGamma\b|\bbroadening\b)\s*>\s*0"
)

_SCI_DOMAINS = {
    "thermal",
    "response",
    "green",
    "mathphys",
    "tensor",
    "sciml",
    "physics",
    "condensed-matter",
}

NEGATIVE_DIR = Path(__file__).resolve().parent / "negative"


def reject_reasons(dossier_dict: dict) -> list[str]:
    """Return taxonomy codes that forbid admission. Empty means not flagged here."""
    if not isinstance(dossier_dict, dict):
        return [UNVERIFIABLE]
    d = {k: v for k, v in dossier_dict.items() if not str(k).startswith("_")}
    found: list[str] = []

    def add(code: str) -> None:
        if code not in found:
            found.append(code)

    if _is_single_add_mul_cse(_text(d.get("expression_sketch"))):
        add(TRIVIAL_CSE)
    if _is_obvious_lgg(d):
        add(OBVIOUS_LGG)
    if _has_leaked_words(d):
        add(TARGET_LEAKED_BY_NOTATION)
    if not _provenance_entries(d):
        add(UNVERIFIABLE)
    if _has_not_declared_analytic(d):
        add(UNDER_SPECIFIED)
    if _is_synthetic_disguised(d):
        add(SYNTHETIC_DISGUISED_AS_SCIENTIFIC)
    if _selected_because_method_works(d):
        add(SELECTED_BECAUSE_METHOD_WORKS)
    if _is_guo(d):
        add(GUO_RESCUE)
    if _silent_physics_positivity(d):
        add(SILENT_PHYSICS_POSITIVITY)
    return found


def load_negative_controls() -> list[tuple[Path, dict[str, Any]]]:
    """Load preserved must-reject dossiers. Does not admit DEV."""
    rows: list[tuple[Path, dict[str, Any]]] = []
    if not NEGATIVE_DIR.is_dir():
        return rows
    for path in sorted(NEGATIVE_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            raise ValueError(f"negative control is not an object: {path}")
        rows.append((path, payload))
    return rows


def _contract(d: dict) -> dict:
    ac = d.get("assumption_contract")
    return ac if isinstance(ac, dict) else {}


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _truthy(value: Any) -> bool:
    if value is True or value == 1:
        return True
    if isinstance(value, str) and value.strip().lower() in {"true", "yes", "1"}:
        return True
    return False


def _walk_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            if str(key).startswith("_"):
                continue
            out.extend(_walk_strings(val))
    elif isinstance(obj, (list, tuple)):
        for val in obj:
            out.extend(_walk_strings(val))
    return out


def _blob(d: dict) -> str:
    return "\n".join(_walk_strings(d))


def _is_guo(d: dict) -> bool:
    if _truthy(d.get("is_guo")):
        return True
    names = " ".join(_text(d.get(k)) for k in ("case_id", "title", "name"))
    return "guo" in names.lower()


def _provenance_entries(d: dict) -> list[str]:
    ac = _contract(d)
    raw = ac.get("source_provenance")
    if raw is None:
        raw = d.get("source_provenance")
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [raw]
    elif isinstance(raw, list):
        items = raw
    else:
        items = [raw]
    return [str(x).strip() for x in items if str(x).strip()]


def _predicates(container: Any) -> list[dict]:
    if not isinstance(container, list):
        return []
    out: list[dict] = []
    for item in container:
        if isinstance(item, dict):
            out.append(item)
        elif isinstance(item, str):
            out.append({"statement": item, "label": NOT_DECLARED, "source": ""})
        else:
            label = getattr(item, "label", NOT_DECLARED)
            statement = getattr(item, "statement", "")
            out.append({"statement": _text(statement), "label": _text(label) or NOT_DECLARED})
    return out


def _label_of(pred: dict) -> str:
    label = pred.get("label", NOT_DECLARED)
    if label is None or str(label).strip() == "":
        return NOT_DECLARED
    return str(label).strip().upper()


def _has_not_declared_analytic(d: dict) -> bool:
    ac = _contract(d)
    for pred in _predicates(ac.get("analytic_domains")):
        if _label_of(pred) == NOT_DECLARED:
            return True
    return False


def _has_leaked_words(d: dict) -> bool:
    blob = _blob(d).lower()
    return any(needle in blob for needle in LEAKED_WORDS)


def _split_top(s: str, sep: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if depth == 0 and s.startswith(sep, i):
            parts.append("".join(buf).strip())
            buf = []
            i += len(sep)
            continue
        buf.append(ch)
        i += 1
    parts.append("".join(buf).strip())
    return parts


def _duplicated_args(args: list[str]) -> bool:
    cleaned = [a.strip() for a in args if a.strip()]
    if len(cleaned) < 2:
        return False
    counts = Counter(cleaned)
    return max(counts.values()) >= 2


def _is_single_add_mul_cse(sketch: str) -> bool:
    s = sketch.strip()
    if not s:
        return False
    for head in ("Add", "Mul"):
        prefix = head + "("
        if s.startswith(prefix) and s.endswith(")"):
            inner = s[len(prefix) : -1].strip()
            if _duplicated_args(_split_top(inner, ",")):
                return True
    for sep in ("+", "*"):
        parts = _split_top(s, sep)
        if _duplicated_args(parts):
            return True
    try:
        import sympy

        expr = sympy.sympify(s, evaluate=False)
        if getattr(expr, "func", None) in (sympy.Add, sympy.Mul):
            args = list(getattr(expr, "args", ()))
            if len(args) >= 2 and max(Counter(args).values()) >= 2:
                return True
    except Exception:
        return False
    return False


def _is_obvious_lgg(d: dict) -> bool:
    # Do not scan why_not_cse_lgg: that field is supposed to mention LGG
    # while denying it.
    claimed = " ".join(
        (
            _text(d.get("latent_structure")),
            _text(d.get("proposed_ladder")),
        )
    ).lower()
    if re.search(r"\blgg\b", claimed) or "least general generalization" in claimed:
        return True
    notes = _text(d.get("notes")).lower()
    return any(n in notes for n in _LGG_NEEDLES)


def _is_synthetic_disguised(d: dict) -> bool:
    if _truthy(d.get("synthetic")):
        return True
    domain = _text(d.get("domain")).strip().lower()
    if domain in _SYNTHETIC_DOMAINS:
        return True
    notes = _text(d.get("notes")).lower()
    license_ = _text(d.get("license")).lower()
    if "synthetic" in notes or "author-constructed" in notes or "author-constructed" in license_:
        if domain in _SCI_DOMAINS or "scientific" in notes:
            return True
    return False


def _selected_because_method_works(d: dict) -> bool:
    blob = " ".join(
        (
            _text(d.get("notes")),
            _text(d.get("why_not_cse_lgg")),
            _text(d.get("proposer_leak_risk")),
        )
    ).lower()
    return any(n in blob for n in _METHOD_WORKS_NEEDLES)


def _declared_positivity_statements(d: dict) -> str:
    ac = _contract(d)
    bits: list[str] = []
    for pred in _predicates(ac.get("positivity_conditions")):
        if _label_of(pred) == "DECLARED":
            bits.append(_text(pred.get("statement")).lower())
    return "\n".join(bits)


def _silent_physics_positivity(d: dict) -> bool:
    ac = _contract(d)
    for pred in _predicates(ac.get("positivity_conditions")):
        if _label_of(pred) == NOT_DECLARED:
            return True
        stmt = _text(pred.get("statement"))
        if _PHYSICS_POS_RE.search(stmt) and _label_of(pred) != "DECLARED":
            return True
    declared = _declared_positivity_statements(d)
    hay = " ".join(
        (
            _text(d.get("notes")),
            _text(d.get("why_not_cse_lgg")),
            _text(d.get("expression_sketch")),
        )
    )
    for match in _PHYSICS_POS_RE.finditer(hay):
        token = re.sub(r"\s+", "", match.group(0)).lower()
        if token not in re.sub(r"\s+", "", declared):
            return True
    return False
