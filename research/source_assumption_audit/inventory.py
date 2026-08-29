"""Inventory frozen Guo domain assumptions. Read-only. No LLM."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SRC = ROOT / "examples" / "long" / "Guo_Sigma_abc_dc_exact.txt"
SYMBOLS = ROOT / "examples" / "long" / "symbols.json"
SOURCE_MD = ROOT / "examples" / "long" / "SOURCE.md"
OUT = HERE / "INVENTORY.json"

HEADER_RE = re.compile(r"\(\*(.*?)\*\)", re.S)


def run() -> dict:
    from research.llm_abstraction.tasks import load_guo_item

    raw = SRC.read_text(encoding="utf-8")
    headers = [m.group(1).strip() for m in HEADER_RE.finditer(raw)]
    symbols_json = json.loads(SYMBOLS.read_text())
    item = load_guo_item()
    item_syms = list(item.get("symbols") or [])

    def flags(entry: dict) -> dict:
        return {
            "name": entry.get("name"),
            "real": entry.get("real"),
            "nonzero": entry.get("nonzero"),
            "positive": entry.get("positive"),
            "integer": entry.get("integer"),
        }

    json_by = {s["name"]: flags(s) for s in symbols_json.get("symbols") or []}
    item_by = {s["name"]: flags(s) for s in item_syms if isinstance(s, dict)}

    positive_declared = [
        n
        for n, f in {**json_by, **item_by}.items()
        if f.get("positive") is True
    ]
    nonzero_declared = [
        n
        for n, f in {**json_by, **item_by}.items()
        if f.get("nonzero") is True
    ]

    report = {
        "source_path": str(SRC.relative_to(ROOT)),
        "source_sha256_documented": "63742cc4e6bf401dd48e258ecb86676b0d7570cc075cae38b91dc188652afc44",
        "headers": headers,
        "header_mentions_beta_positive": any("beta" in h.lower() and "positive" in h.lower() for h in headers),
        "header_mentions_gamma_positive": any(
            ("gamma" in h.lower() or "gamma treatment" in h.lower()) and ">" in h
            for h in headers
        ),
        "finite_gamma_phrase": any("exact finite Gamma" in h for h in headers),
        "symbols_json": json_by,
        "load_guo_item_symbols": item_by,
        "load_guo_item_required_assumptions": item.get("required_assumptions"),
        "positive_declared": positive_declared,
        "nonzero_declared": nonzero_declared,
        "beta_json": json_by.get("beta"),
        "gamma_json": json_by.get("gamma"),
        "mu_json": json_by.get("mu"),
        "ingestion_default": (
            "Wolfram translator: symbols real unless listed complex; "
            "nonzero only if passed in nonzero_symbols (empty at load_guo_item)."
        ),
        "denominator_gamma_is_not_a_declaration": True,
        "no_llm": True,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


if __name__ == "__main__":
    r = run()
    print(json.dumps({
        "positive_declared": r["positive_declared"],
        "nonzero_declared": r["nonzero_declared"],
        "required_assumptions": r["load_guo_item_required_assumptions"],
        "beta": r["beta_json"],
        "gamma": r["gamma_json"],
        "finite_gamma_phrase": r["finite_gamma_phrase"],
    }, indent=2))
