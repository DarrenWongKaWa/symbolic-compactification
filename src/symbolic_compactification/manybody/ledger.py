"""A derivation written down step by step: "Eq. X -> Eq. Y, using R".

Most steps of a paper are not written inside one display. The paper shows
Eq. (59), says "we reorganize K_1A and apply the metric-velocity relation",
and shows Eq. (60). An assistant or a person records that step in a ledger;
the tool checks it. Every formula in the ledger is a verbatim quote of the
paper, read by two readers (``dualread``); nothing is retyped.

    source_document: paper.tex            # relative to this file
    include: conventions.yaml             # optional: symbols, notation, definitions
    steps:
      - id: K1A-metric
        from: {display: "eq:D60", quote: "v_1^c(v_{21}^a v_{12}^b + ...)"}
        to:   {display: "eq:D60", quote: "2\\epsilon_{12}^2 (v_1^c g_{ab} + v_1^b g_{ac})"}
        given:                            # relations the step uses, quoted from the text
          - quote: "v_{12}^a v_{21}^b + v_{12}^b v_{21}^a = 2\\epsilon_{12}^2 g_{ab}"
            instances: [{}, {b: c}]       # also with the index b renamed to c
        under: "\\sum_n"                  # optional: both sides sit under this sum
        note: "we reorganize K_1A and apply the metric-velocity relation"

Each step becomes one step card (``check: identity``) and is decided like
any other card: VALID only on an engine ZERO, with or without the stated
relations; the relations used are listed with the verdict, never proved.
"""
from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .cards import CardError

LEDGER_KEYS = frozenset({"source_document", "include", "steps"})
STEP_KEYS = frozenset({"id", "type", "from", "to", "given", "under", "note", "noncommuting"})
# what kind of move a step is; the tool checks only algebra (and algebra on summands,
# term by term). Every other step is left to the reviewer, with its type.
CHECKED_TYPES = ("algebra", "sum-termwise")
STEP_TYPES = (*CHECKED_TYPES, "integral", "limit", "approximation", "definition")
SIDE_KEYS = frozenset({"quote", "display"})
GIVEN_KEYS = frozenset({"quote", "display", "instances"})


def _check_keys(entry: Any, allowed: frozenset, where: str) -> dict:
    if not isinstance(entry, dict):
        raise CardError(f"{where} must be a mapping")
    unknown = sorted(set(entry) - allowed)
    if unknown:                    # a misspelled key must not be ignored silently
        raise CardError(f"{where}: unknown key(s) {', '.join(unknown)}; allowed: {', '.join(sorted(allowed))}")
    return entry


def load_ledger(path: str | Path) -> dict:
    path = Path(path)
    ledger = _check_keys(yaml.safe_load(path.read_text(encoding="utf-8")) or {}, LEDGER_KEYS, "ledger")
    if not ledger.get("source_document"):
        raise CardError("ledger needs source_document")
    include = ledger.get("include")
    if include is not None:
        parts = Path(str(include)).parts
        if not isinstance(include, str) or Path(include).is_absolute() or ".." in parts:
            # it is copied into the reviewer package: it must be the ledger's own file
            raise CardError("include must be a file next to the ledger (no absolute path, no '..')")
    steps = ledger.get("steps")
    if not isinstance(steps, list) or not steps:
        raise CardError("ledger needs a non-empty list of steps")
    seen: set[str] = set()
    for k, step in enumerate(steps):
        _check_keys(step, STEP_KEYS, f"step {k + 1}")
        ident = str(step.get("id") or "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,100}", ident):
            raise CardError(f"step {k + 1}: id must be letters, digits, '.', '_', ':' or '-'")
        if ident in seen:
            raise CardError(f"step {ident}: id used twice")
        if step.get("type") not in STEP_TYPES:
            raise CardError(f"step {ident}: type must be one of {', '.join(STEP_TYPES)}")
        seen.add(ident)
        for side in ("from", "to"):
            entry = _check_keys(step.get(side), SIDE_KEYS, f"step {ident}: {side}")
            if not str(entry.get("quote") or "").strip():
                raise CardError(f"step {ident}: {side} needs a quote")
        given = step.get("given") or []
        if not isinstance(given, list):
            raise CardError(f"step {ident}: given must be a list")
        for g in given:
            entry = _check_keys(g if isinstance(g, dict) else {"quote": g}, GIVEN_KEYS, f"step {ident}: given")
            instances = entry.get("instances", [{}])
            if not isinstance(instances, list) or not all(isinstance(i, dict) for i in instances):
                raise CardError(f"step {ident}: instances must be a list of renamings like {{b: c}}")
        if "noncommuting" in step and step["noncommuting"] is not False:
            raise CardError(f"step {ident}: noncommuting may only be set to false (with a note why)")
        if "noncommuting" in step and not str(step.get("note") or "").strip():
            raise CardError(f"step {ident}: noncommuting: false needs a note saying why")
    return ledger


def _relative(target: Path, start: Path) -> str:
    return os.path.relpath(target.resolve(), start.resolve())


def step_card(step: dict, *, source_document: str, include: list[str]) -> dict:
    """One ledger step as a step card (paths relative to the cards directory)."""
    card: dict[str, Any] = {
        "check": "identity",
        "label": str(step["id"]),
        **({"include": include} if include else {}),
        "source_document": source_document,
        "source": {"lhs": {k: step["from"][k] for k in ("quote", "display") if step["from"].get(k)},
                   "rhs": {k: step["to"][k] for k in ("quote", "display") if step["to"].get(k)}},
        "step": {"type": step["type"], "from": step["from"].get("display"), "to": step["to"].get("display"),
                 **({"note": str(step["note"])} if step.get("note") else {})},
    }
    if step.get("given"):
        card["given"] = [g if isinstance(g, dict) else {"quote": g} for g in step["given"]]
    if step.get("under"):
        card["under"] = str(step["under"])
    if "noncommuting" in step:
        card["noncommuting"] = False
    return card


def locate_display(raw: str, quote: str) -> str | None:
    """The one display (its \\label, else #n) holding the quote, or None when
    no display or several hold it."""
    from .fidelity import _displays, _whole_occurrence
    from .latex import layout_free, layout_rows
    hits = []
    for key, (text, _) in _displays(raw).items():
        if key.startswith("#") and _whole_occurrence(layout_free(quote), layout_rows(text)):
            hits.append(key)
    if len(hits) != 1:
        return None
    labels = [k for k, (text, _) in _displays(raw).items()
              if not k.startswith("#") and text == _displays(raw)[hits[0]][0]]
    return labels[0] if labels else hits[0]


def _with_displays(step: dict, raw: str) -> dict:
    """Fill in the display of each side the ledger leaves out."""
    step = dict(step)
    for side in ("from", "to"):
        entry = dict(step[side])
        if not entry.get("display"):
            found = locate_display(raw, str(entry["quote"]))
            if found:
                entry["display"] = found
        step[side] = entry
    return step


def card_name(ident: str) -> str:
    return "ledger." + re.sub(r"[^A-Za-z0-9_.-]", "_", ident) + ".yaml"


def write_cards(ledger_path: str | Path, cards_dir: str | Path, *, document: Path | None = None) -> list[Path]:
    """Write one card per ledger step into ``cards_dir``, next to the paper's
    drafted ``conventions.yaml`` (which carries what the text says about its
    symbols: matrices, constraints, named quantities). The ledger's own
    ``include:`` is added after it; a conflict between the two blocks the step.
    ``document`` overrides the ledger's source_document (a review workspace
    keeps its own copy of the paper)."""
    ledger_path, cards_dir = Path(ledger_path), Path(cards_dir)
    ledger = load_ledger(ledger_path)
    doc = document or (ledger_path.parent / str(ledger["source_document"]))
    if not doc.exists():
        raise CardError(f"source_document not found: {doc}")
    cards_dir.mkdir(parents=True, exist_ok=True)
    if not (cards_dir / "conventions.yaml").exists():
        _conventions_for(doc, cards_dir)
    include = ["conventions.yaml"]
    if ledger.get("include"):
        own = ledger_path.parent / str(ledger["include"])
        copy = cards_dir / "includes" / ("ledger-" + re.sub(r"[^A-Za-z0-9_.-]", "_", own.name))
        copy.parent.mkdir(exist_ok=True)           # not a card: review reads cards/*.yaml only
        shutil.copyfile(own, copy)                 # a reviewer package must hold every file it reads
        include.append(f"includes/{copy.name}")
    for old in cards_dir.glob("ledger.*.yaml"):        # the ledger is the source of these cards
        old.unlink()
    raw = doc.read_text(encoding="utf-8")
    written = []
    for step in ledger["steps"]:
        if step["type"] not in CHECKED_TYPES:
            continue                             # left to the reviewer: no card
        card = step_card(_with_displays(step, raw), source_document=_relative(doc, cards_dir),
                         include=include)
        path = cards_dir / card_name(str(step["id"]))
        path.write_text("# From the step ledger " + ledger_path.name + "; edit the ledger, not this card.\n"
                        + yaml.safe_dump(card, sort_keys=False, allow_unicode=True), encoding="utf-8")
        written.append(path)
    return written


def _conventions_for(document: Path, cards_dir: Path) -> None:
    """Draft the paper's conventions (symbols, notation, definitions) once."""
    from .draft import draft
    with tempfile.TemporaryDirectory() as tmp:
        draft(document, Path(tmp) / "cards")
        shutil.copyfile(Path(tmp) / "cards" / "conventions.yaml", cards_dir / "conventions.yaml")


def run_ledger(ledger_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    """Compile the ledger into ``out_dir/cards`` and decide every step."""
    from .cards import run_card
    ledger_path, out = Path(ledger_path), Path(out_dir)
    ledger = load_ledger(ledger_path)
    cards_dir = out / "cards"
    rows = []
    checked = [step for step in ledger["steps"] if step["type"] in CHECKED_TYPES]
    for step in ledger["steps"]:
        if step["type"] not in CHECKED_TYPES:
            rows.append(reviewer_row(step))
    for path, step in zip(write_cards(ledger_path, cards_dir), checked):
        located = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("step") or {}
        try:
            result = run_card(path, require_source=True)
        except Exception as exc:          # one step must never stop the others
            result = {"decision": "NOT_DECIDED", "status": "UNKNOWN",
                      "decision_blocked_by": [f"STEP_ERROR:{type(exc).__name__}:{str(exc)[:120]}"]}
        rows.append(step_row(step, result, located))
    order = {str(step["id"]): k for k, step in enumerate(ledger["steps"])}
    rows.sort(key=lambda r: order[r["step"]])
    return {"ledger": str(ledger_path), "cards": str(cards_dir), "steps": rows,
            "counts": {k: sum(1 for r in rows if r["decision"] == k)
                       for k in ("VALID", "INVALID", "NOT_DECIDED", "NEEDS_REVIEWER")},
            "types": {t: sum(1 for r in rows if r["type"] == t) for t in STEP_TYPES}}


def reviewer_row(step: dict) -> dict[str, Any]:
    """A step the tool does not check (an integral, a limit, an approximation, a
    definition): left to the reviewer, with its type and quotes."""
    return {"step": str(step["id"]), "type": step["type"],
            "from": step["from"].get("display"), "to": step["to"].get("display"),
            "decision": "NEEDS_REVIEWER", "status": None, "holds_given": [], "why_not_decided": [],
            "quotes": {"from": step["from"]["quote"], "to": step["to"]["quote"]}}


def step_row(step: dict, result: dict, located: dict | None = None) -> dict[str, Any]:
    given = result.get("given") or []
    located = located or {}
    return {
        "step": str(step["id"]),
        "type": step["type"],
        "from": located.get("from") or step["from"].get("display"),
        "to": located.get("to") or step["to"].get("display"),
        "decision": result["decision"],
        "status": result.get("status") or result.get("verdict"),
        "holds_given": [{"quote": g["quote"], **({"rename": g["rename"]} if g.get("rename") else {})}
                        for g in given if g.get("used")],
        **({"under": step["under"]} if step.get("under") else {}),
        **({"one_sided_symbols": result["one_sided_symbols"]} if result.get("one_sided_symbols") else {}),
        "why_not_decided": list(result.get("decision_blocked_by") or []) or (
            list(result.get("reasons") or []) if result["decision"] == "NOT_DECIDED" else []),
        **({"certificate": result["certificate"]} if result.get("certificate") else {}),
        **({"counterexample": result["counterexample"]} if result.get("counterexample") else {}),
    }
