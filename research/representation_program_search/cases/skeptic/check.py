"""Reject miner dossiers that fail the representation-search skeptic.

Not search. Negative controls must not enter DEV/TEST/CHALLENGE.
Guo remains sealed.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

RENAMED_OLD_DEV_TEST = "RENAMED_OLD_DEV_TEST"
SYNTAX_REVEALS_TARGET = "SYNTAX_REVEALS_TARGET"
TRIVIAL_CSE = "TRIVIAL_CSE"
FIRST_ORDER_LGG_ONLY = "FIRST_ORDER_LGG_ONLY"
UNVERIFIABLE_DOMAIN = "UNVERIFIABLE_DOMAIN"
FABRICATED_TOY = "FABRICATED_TOY"
GRAMMAR_BAIT = "GRAMMAR_BAIT"
GUO_SEALED = "GUO_SEALED"

NOT_DECLARED = "NOT_DECLARED"

REASON_CODES = (
    RENAMED_OLD_DEV_TEST,
    SYNTAX_REVEALS_TARGET,
    TRIVIAL_CSE,
    FIRST_ORDER_LGG_ONLY,
    UNVERIFIABLE_DOMAIN,
    FABRICATED_TOY,
    GRAMMAR_BAIT,
    GUO_SEALED,
)

# Frozen AC identities from HISTORICAL_DIAGNOSTIC.md (expanded ranges).
FORBIDDEN_HISTORICAL_IDS = (
    "mp-resolvent-dd-01",
    "mp-daleckii-krein-01",
    "mp-hermite-fA-01",
    "mp-cauchy-dunford-01",
    "thermal-01-fermi-im-digamma",
    "thermal-01",
    "thermal-03-digamma-reflection",
    "thermal-03",
    "thermal-05-trigamma-double-pole",
    "thermal-05",
    "sciml-phi-hermite-01",
    "sciml-vanloan-blockexp-01",
    "sciml-daleckii-krein-01",
    "ac-t-eps-delta",
    "ac-t-young-s3",
    "ac-r01-resolvent-hilbert-identity",
    "ac-r01",
    "mp-kato-simple-ev-01",
    "mp-parlett-schur-01",
    "sciml-tweedie-gauss-01",
    "sciml-ou-mehler-01",
    "sciml-deq-ift-01",
    "sciml-adjoint-linear-01",
    "ac-t-weyl-su2-char",
    "ac-t-ricci-weyl",
    "ac-t-clebsch-half",
    "ac-t-iso4-projectors",
    "thermal-02-bose-im-digamma",
    "thermal-02",
    "thermal-04-coth-matsubara",
    "thermal-04",
    "thermal-06-fermi-dirac-polylog",
    "thermal-06",
    "thermal-07-green-spectral-hilbert",
    "thermal-07",
    "thermal-08-matsubara-newton-dd-underspecified",
    "thermal-08",
    "mp-mathias-block-01",
    "mp-opitz-dd-01",
    "ac-r02-sokhotski-plemelj-boundary",
    "ac-r02",
    "ac-r04-lindhard-occupation-dd",
    "ac-r04",
    "ac-r05-lehmann-spectral-master",
    "ac-r05",
    "ac-r06-matsubara-pole-family",
    "ac-r06",
    "ac-r07-lippmann-schwinger-iepsilon",
    "ac-r07",
    "ac-r08-kubo-frequency-underspecified",
    "ac-r08",
    "sciml-lyapunov-kronecker-01",
    "ac-t-pauli-completeness",
    "ac-t-rej-index-rename",
    "nc-guo-sigma-abc",
)

# Proposer-visible leak needles (sketch / catalog / title / proposer_view).
_LEAK_NEEDLES = (
    "hermite_dd",
    "newton_dd",
    "add_hermite_dd",
    "add_newton_dd",
    "gold program",
    "gold operator",
    "target representation",
    "the master function is",
    "phi_gamma",
    "hermite interpolant",
    "hermite-on-guo",
    "hermite divided difference",
    "newton divided difference",
)

_HERMITE_NAME_RE = re.compile(r"\bhermite\b", re.I)

_LGG_NEEDLES = (
    "least general generalization",
    "least-general generalization",
    "obvious lgg",
    "frozen lgg",
    "first-order lgg",
    "first-order anti-unification",
    "first order anti-unification",
)

_GRAMMAR_BAIT_NEEDLES = (
    "grammar bait",
    "grammar-bait",
    "representationgrammarv1",
    "fit representationgrammarv1",
    "fits representationgrammarv1",
    "chosen specifically to fit",
    "selected to fit the grammar",
    "selected because representationgrammarv1",
    "because hermite_dd",
    "because newton_dd",
    "named hermite",
    "g_full will succeed",
    "newton_dd/hermite_dd bait",
    "hermite_dd bait",
    "newton_dd bait",
    "hermite_dd as a primitive",
    "newton_dd as a primitive",
)

_SYNTHETIC_DOMAINS = {
    "synthetic",
    "toy",
    "generated",
    "author-constructed",
    "author_constructed",
}

_SCI_DOMAINS = {
    "thermal",
    "response",
    "green",
    "mathphys",
    "matrix",
    "tensor",
    "diffphys",
    "sciml",
    "physics",
    "condensed-matter",
}

_TOY_NEEDLES = (
    "fabricated",
    "author-constructed toy",
    "author-constructed",
    "hand-built polynomial",
    "hand-built interpolant",
    "disguised as",
    "looks like physics",
    "no scientific source",
)

SKEPTIC_DIR = Path(__file__).resolve().parent
NEGATIVE_DIR = SKEPTIC_DIR / "negative"
INDEX_PATH = SKEPTIC_DIR / "index.json"


def reject_reasons(dossier_dict: dict) -> list[str]:
    """Return taxonomy codes that forbid admission. Empty means not flagged here."""
    if not isinstance(dossier_dict, dict):
        return [UNVERIFIABLE_DOMAIN]
    d = {k: v for k, v in dossier_dict.items() if not str(k).startswith("_")}
    found: list[str] = []

    def add(code: str) -> None:
        if code not in found:
            found.append(code)

    if _is_renamed_historical(d):
        add(RENAMED_OLD_DEV_TEST)
    if _syntax_reveals_target(d):
        add(SYNTAX_REVEALS_TARGET)
    if _is_single_add_mul_cse(_text(d.get("expression_sketch"))):
        add(TRIVIAL_CSE)
    if _is_first_order_lgg(d):
        add(FIRST_ORDER_LGG_ONLY)
    if _unverifiable_domain(d):
        add(UNVERIFIABLE_DOMAIN)
    if _is_fabricated_toy(d):
        add(FABRICATED_TOY)
    if _is_grammar_bait(d):
        add(GRAMMAR_BAIT)
    if _is_guo(d):
        add(GUO_SEALED)
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


def load_index() -> dict[str, Any]:
    with INDEX_PATH.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError("skeptic index.json is not an object")
    return payload


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


def _is_guo(d: dict) -> bool:
    if _truthy(d.get("is_guo")):
        return True
    names = " ".join(_text(d.get(k)) for k in ("case_id", "title", "name"))
    return "guo" in names.lower()


def _id_mentioned(blob: str, fid: str) -> bool:
    if not blob or not fid:
        return False
    pattern = re.compile(
        r"(?<![a-z0-9])" + re.escape(fid.lower()) + r"(?![a-z0-9])",
        re.I,
    )
    return pattern.search(blob) is not None


def _historical_blob(d: dict) -> str:
    bits = [
        _text(d.get("case_id")),
        _text(d.get("title")),
        _text(d.get("name")),
        _text(d.get("historical_parent")),
        _text(d.get("renamed_from")),
        _text(d.get("notes")),
    ]
    ids = d.get("historical_ids")
    if isinstance(ids, str):
        bits.append(ids)
    elif isinstance(ids, (list, tuple)):
        bits.extend(_text(x) for x in ids)
    return "\n".join(bits)


def _is_renamed_historical(d: dict) -> bool:
    blob = _historical_blob(d)
    for fid in FORBIDDEN_HISTORICAL_IDS:
        if _id_mentioned(blob, fid):
            return True
    parent = _text(d.get("historical_parent")).strip()
    if parent and parent in FORBIDDEN_HISTORICAL_IDS:
        return True
    return False


def _proposer_visible(d: dict) -> str:
    bits = [
        _text(d.get("expression_sketch")),
        _text(d.get("title")),
        _text(d.get("proposer_view")),
        _text(d.get("source_catalog")),
    ]
    catalog = d.get("catalog")
    if isinstance(catalog, (dict, list, tuple, str)):
        bits.extend(_walk_strings(catalog))
    return "\n".join(bits)


def _syntax_reveals_target(d: dict) -> bool:
    blob = _proposer_visible(d).lower()
    if any(needle in blob for needle in _LEAK_NEEDLES):
        return True
    return _HERMITE_NAME_RE.search(blob) is not None


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
            out.append(
                {
                    "statement": _text(statement),
                    "label": _text(label) or NOT_DECLARED,
                }
            )
    return out


def _label_of(pred: dict) -> str:
    label = pred.get("label", NOT_DECLARED)
    if label is None or str(label).strip() == "":
        return NOT_DECLARED
    return str(label).strip().upper()


def _has_not_declared_analytic(d: dict) -> bool:
    ac = _contract(d)
    domains = ac.get("analytic_domains")
    if domains is None:
        return False
    preds = _predicates(domains)
    if not preds:
        return False
    for pred in preds:
        if _label_of(pred) == NOT_DECLARED:
            return True
    return False


def _unverifiable_domain(d: dict) -> bool:
    if not _provenance_entries(d):
        return True
    return _has_not_declared_analytic(d)


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


def _is_first_order_lgg(d: dict) -> bool:
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
    if "first-order anti-unification" in claimed:
        return True
    notes = _text(d.get("notes")).lower()
    return any(n in notes for n in _LGG_NEEDLES)


def _is_fabricated_toy(d: dict) -> bool:
    if _truthy(d.get("synthetic")):
        return True
    domain = _text(d.get("domain")).strip().lower()
    if domain in _SYNTHETIC_DOMAINS:
        return True
    notes = _text(d.get("notes")).lower()
    license_ = _text(d.get("license")).lower()
    hay = notes + "\n" + license_
    if any(n in hay for n in _TOY_NEEDLES):
        if domain in _SCI_DOMAINS or "scientific" in notes:
            return True
    return False


def _is_grammar_bait(d: dict) -> bool:
    if _truthy(d.get("grammar_bait")):
        return True
    blob = " ".join(
        (
            _text(d.get("notes")),
            _text(d.get("why_not_cse_lgg")),
            _text(d.get("selection_reason")),
            _text(d.get("proposer_leak_risk")),
        )
    ).lower()
    return any(n in blob for n in _GRAMMAR_BAIT_NEEDLES)
