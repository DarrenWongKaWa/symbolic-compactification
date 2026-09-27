"""One command from a LaTeX paper to a reviewer package.

    symbolic-compactification manybody review paper.tex --out review/

1. Copies the paper into ``review/manuscript/source.tex`` and drafts one
   step card per displayed relation into ``review/cards/``.
2. Writes the audit workspace: every card is a STEP_CARD edge, and every
   card's source equation is an entry of the equation manifest.
3. Runs ``audit verify``, ``audit report`` and ``audit package`` with the
   strict source replay.
4. Returns one row per step (decision, check, equation, line) and the path
   of ``REVIEWER_SUMMARY.html``.

Running it again on the same ``--out`` keeps ``cards/`` (the user may
have edited conventions.yaml or a card's check) and only re-verifies.
"""
from __future__ import annotations

import io
import json
import re
import shutil
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import yaml

from .draft import draft

_AUDIT_YAML = """schema_version: DerivationAuditV1
audit_name: {name}
manuscript_source: manuscript/{source}
equation_manifest: equations/equations.yaml
edge_manifest: edges/edges.yaml
assumptions: assumptions/assumptions.yaml
output_dir: reports
verifier_profile: python_sympy_exact_v1
"""


def _slug(text: str) -> str:
    keep = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in text)
    return keep.strip("-.") or "paper"


def _workspace(out: Path, document: Path) -> None:
    for sub in ("manuscript", "cards", "equations", "edges", "assumptions", "reports", "runs"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(document, out / "manuscript" / _source_name(document))
    audit = out / "audit.yaml"
    if not audit.exists():
        audit.write_text(_AUDIT_YAML.format(name=_slug(document.stem) + "-review",
                                            source=_source_name(document)), encoding="utf-8")


def _source_name(document: Path) -> str:
    """source.tex for LaTeX, source.md / source.txt for plain-text sheets."""
    return "source" + (document.suffix.lower() or ".txt")


def _manifests(out: Path, source_name: str = "source.tex") -> list[dict[str, Any]]:
    """Equation and edge manifests from the cards (rewritten on every run)."""
    from .cards import run_card
    cards = sorted(p for p in (out / "cards").glob("*.yaml") if p.name != "conventions.yaml")
    equations, edges, rows = [], [], []
    seen: set[str] = set()
    for path in cards:
        card = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        ident = _ident(str(card.get("label") or path.stem), seen)
        eq_id = ident
        equations.append({"equation_id": eq_id, "label": ident, "environment": "equation",
                          "source_file": f"manuscript/{source_name}", "curated": True,
                          "body": str((card.get("source") or {}).get("rhs")
                                      or (card.get("source") or {}).get("claim") or path.stem)[:400]})
        edges.append({"edge_id": ident, "source_from": eq_id, "source_to": eq_id,
                      "edge_type": "STEP_CARD", "step_card": {"card": f"cards/{path.name}"},
                      "claim": f"displayed relation {path.stem} as printed"})
        rows.append({"card": ident, "path": path})
    (out / "equations" / "equations.yaml").write_text(yaml.safe_dump(
        {"schema_version": "DerivationAuditV1", "equations": equations}, sort_keys=False), encoding="utf-8")
    (out / "edges" / "edges.yaml").write_text(yaml.safe_dump(
        {"schema_version": "DerivationAuditV1", "edges": edges}, sort_keys=False), encoding="utf-8")
    conventions = yaml.safe_load((out / "cards" / "conventions.yaml").read_text(encoding="utf-8")) \
        if (out / "cards" / "conventions.yaml").exists() else {}
    from ..models import AdapterError, normalize_symbols
    from ..parser import _DEFAULT_POLICY
    symbols = []
    for entry in (conventions or {}).get("symbols") or []:       # the audit only records these;
        name = str(entry["name"] if isinstance(entry, dict) else entry)   # cards carry their own
        if isinstance(entry, dict) and entry.get("real") is False:
            continue          # complex symbols are carried by the cards; the audit file lists real ones
        candidate = {"name": name, "real": True, "nonzero": False}
        try:
            normalize_symbols([candidate])
        except AdapterError:
            continue
        symbols.append(candidate)
    symbols = symbols[:int(_DEFAULT_POLICY["max_symbols"])]
    (out / "assumptions" / "assumptions.yaml").write_text(yaml.safe_dump(
        {"symbols": symbols or [{"name": "x", "real": True, "nonzero": False}], "functions": []},
        sort_keys=False), encoding="utf-8")
    return rows


def _ident(label: str, seen: set[str]) -> str:
    """The paper's own label (eq:bubble) as the audit id, made unique."""
    base = re.sub(r"[^A-Za-z0-9._:-]", "-", label).strip("-.:") or "step"
    if not re.match(r"[A-Za-z0-9]", base):
        base = "s" + base
    ident, k = base[:120], 2
    while ident in seen:
        ident, k = f"{base[:115]}-{k}", k + 1
    seen.add(ident)
    return ident


def _cli(*argv: str) -> int:
    from .. import cli
    with redirect_stdout(io.StringIO()):
        return cli.main(list(argv))


def review(document: str | Path, out_dir: str | Path) -> dict[str, Any]:
    document, out = Path(document).resolve(), Path(out_dir).resolve()
    fresh = not (out / "cards" / "conventions.yaml").exists()
    _workspace(out, document)
    drafted = draft(out / "manuscript" / _source_name(document), out / "cards") if fresh else None
    rows = _manifests(out, _source_name(document))
    verify = _cli("audit", "verify", str(out))
    _cli("audit", "report", str(out))
    _cli("audit", "package", str(out))
    records_path = out / "reviewer-verification-package" / "machine_results" / "machine_records.json"
    records = json.loads(records_path.read_text(encoding="utf-8")) if records_path.exists() else []
    records = records.get("records", records) if isinstance(records, dict) else records
    by_edge = {r["edge_id"]: r for r in records}
    decision_of = {"CERTIFIED_BY_RULE": "VALID", "NONZERO": "INVALID"}
    steps = []
    for row in rows:
        rec = by_edge.get(row["card"], {})
        warn = rec.get("warnings", [])
        at = next((w.split(":", 1)[1] for w in warn if w.startswith("SOURCE_AT:")), "")
        _, line, label, number = (at.split("|") + ["", "", "", ""])[:4]
        steps.append({
            "step": row["card"], "decision": decision_of.get(rec.get("status"), "NOT_DECIDED"),
            "status": rec.get("status"),
            "check": next((w.split(":", 1)[1] for w in warn if w.startswith("CARD_CHECK:")), None),
            "after_erratum": next((w.split(":", 1)[1] for w in warn if w.startswith("WITH_ERRATUM:")), None),
            "why_not_decided": [w.split(":", 1)[1] for w in warn if w.startswith("BLOCKED:")]
            or ([r for r in warn if not r.startswith(("CARD_", "TRANSCRIPTION", "QUOTE", "READ_AS",
                                                      "DERIVED", "SOURCE_AT", "COUNTEREXAMPLE",
                                                      "DIAGNOSIS", "PRINTED", "ERRATUM", "WITH_"))][:3]
                if rec.get("status") not in decision_of else []),
            "label": label or None, "equation": number or None, "line": int(line) if line else None})
    steps.sort(key=lambda s: (s["line"] is None, s["line"] or 0, s["step"]))
    html = out / "reviewer-verification-package" / "REVIEWER_SUMMARY.html"
    todo = (drafted or {}).get("unresolved_tokens", [])
    conv = yaml.safe_load((out / "cards" / "conventions.yaml").read_text(encoding="utf-8")) or {}
    assumed_real = [s["name"] for s in conv.get("symbols") or []
                    if isinstance(s, dict) and "real" not in s and not s.get("positive")]
    kept_complex = [s["name"] for s in conv.get("symbols") or [] if isinstance(s, dict) and s.get("real") is False]
    assumed = {
        "assumed_real": assumed_real,
        "complex": kept_complex,
        "positive": [{"name": s["name"], "stated": s.get("stated", "not stated in the text")}
                     for s in conv.get("symbols") or [] if isinstance(s, dict) and s.get("positive")],
        "multiply": list(conv.get("multiply") or []),
        "notation": dict(conv.get("notation") or {}),
    }
    verify_meaning = {0: "audit ran; no step is INVALID", 2: "audit ran; some steps are INVALID (NONZERO)"}
    return {
        "document": str(document), "workspace": str(out), "html": str(html) if html.exists() else None,
        "verify": verify_meaning.get(verify, f"audit verify failed (exit {verify}); see the workspace"),
        "assumptions_to_confirm": assumed, "steps": steps,
        "counts": {k: sum(1 for s in steps if s["decision"] == k) for k in ("VALID", "INVALID", "NOT_DECIDED")},
        "how_to_read": ("Report each step's `decision` (VALID / INVALID / NOT_DECIDED); `status` is "
                        "the audit record behind it. Send `html` to a colleague: it is the "
                        "self-contained reviewer page of the replayable package."),
        "next": ("Every VALID/INVALID above was decided by the tool from verbatim quotes, under "
                 "assumptions_to_confirm (guessed from the text; check them against the paper). "
                 "NOT_DECIDED steps are outside the supported forms or need conventions: edit "
                 f"{out / 'cards' / 'conventions.yaml'} (symbols, notation, definitions) or a card's "
                 "check, then run the same command again."
                 + (f" Unresolved tokens: {', '.join(todo[:20])}." if todo else "")),
    }
