"""Generic Laurent suite. FALSE ZERO = 0. Numeric agreement is not ZERO."""
from __future__ import annotations

import json
from pathlib import Path

import sympy

from research.coefficient_laurent.schema import (
    NONZERO,
    UNKNOWN,
    ZERO,
    compose_hop_verdict,
)

OUT = Path(__file__).resolve().parents[1] / "GENERIC_SUITE.json"
MD = Path(__file__).resolve().parents[1] / "GENERIC_SUITE.md"

x, y, t = sympy.symbols("x y t")


def _row(i, expect, got, note=""):
    return {"id": i, "expect": expect, "got": got, "ok": got == expect, "note": note}


def run() -> dict:
    rows = []
    # A/B: removable pole, t^0 matches
    v, _ = compose_hop_verdict(
        reconstruction_ok=True, atoms_expanded=True,
        negative_verdict=ZERO, constant_verdict=ZERO, remainder_verdict=ZERO,
    )
    rows.append(_row("B-full-cancel", ZERO, v))
    # C: t^0 matches, t^-1 survives
    v, _ = compose_hop_verdict(
        reconstruction_ok=True, atoms_expanded=True,
        negative_verdict=NONZERO, constant_verdict=ZERO, remainder_verdict=ZERO,
    )
    rows.append(_row("C-surviving-pole", NONZERO, v))
    # D sign / E wrong order -> not ZERO if constant NONZERO
    v, _ = compose_hop_verdict(
        reconstruction_ok=True, atoms_expanded=True,
        negative_verdict=ZERO, constant_verdict=NONZERO, remainder_verdict=ZERO,
    )
    rows.append(_row("E-wrong-order", NONZERO, v))
    # LEVEL A only
    v, _ = compose_hop_verdict(
        reconstruction_ok=True, atoms_expanded=True,
        negative_verdict=UNKNOWN, constant_verdict=UNKNOWN, remainder_verdict=UNKNOWN,
    )
    rows.append(_row("A-atoms-only-not-zero", UNKNOWN, v))
    n_false = sum(1 for r in rows if r["got"] == ZERO and r["expect"] != ZERO)
    report = {"n": len(rows), "false_ZERO": n_false, "pass": n_false == 0 and all(r["ok"] for r in rows), "rows": rows}
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# V5 generic suite", "", f"false ZERO = {n_false}", ""]
    for r in rows:
        lines.append(f"- {r['id']}: expect {r['expect']} got {r['got']} ok={r['ok']}")
    MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps({k: run()[k] for k in ("n", "false_ZERO", "pass")}))
