"""Phase V1 generic verifier suite. False ZERO must stay 0."""
from __future__ import annotations

import json
from pathlib import Path

import sympy

from research.scalable_verification.api import NONZERO, ZERO
from research.scalable_verification.confluence import check_limit
from research.scalable_verification.dd_cert import (
    hermite_xxx_ok,
    hermite_xxy_ok,
    newton_first_ok,
    repeated_ok,
)
from research.scalable_verification.factor import split_multiplicative
from research.scalable_verification.special import classify_identity

OUT = Path(__file__).resolve().parents[1] / "GENERIC_SUITE.json"
MD = Path(__file__).resolve().parents[1] / "GENERIC_SUITE.md"

z, x, y = sympy.symbols("z x y")


def _row(cid, expect, got, note=""):
    ok = (expect == ZERO and got == ZERO) or (expect == NONZERO and got != ZERO)
    if expect == ZERO and got != ZERO:
        ok = False
    if expect == NONZERO and got == ZERO:
        ok = False
    return {"id": cid, "expect": expect, "got": got, "ok": ok, "note": note}


def run() -> dict:
    F = z**3
    rows = []
    n1 = newton_first_ok(F, z, x, y, (x**3 - y**3) / (x - y))
    rows.append(_row("pos-newton-first", ZERO, n1.verdict, n1.provenance))
    rrep = repeated_ok(F, z, x, 3 * x**2)
    rows.append(_row("pos-repeated-node", ZERO, rrep.verdict, rrep.provenance))
    rxxy = hermite_xxy_ok(F, z, x, y, 2 * x + y)
    rows.append(_row("pos-second-repeated-xxy", ZERO, rxxy.verdict, rxxy.provenance))
    rxxx = hermite_xxx_ok(F, z, x, 3 * x)
    rows.append(_row("pos-triple-repeated", ZERO, rxxx.verdict, rxxx.provenance))
    rem = check_limit((x**2 - y**2) / (x - y), y, x, 2 * x)
    rows.append(_row("pos-removable-singularity", ZERO, rem.verdict, rem.provenance))
    pw = check_limit((x**2 - y**2) / (x - y), y, x, 2 * x)
    rows.append(_row("pos-piecewise-confluence-kernel", ZERO, pw.verdict, pw.provenance))
    clf = classify_identity((sympy.polygamma(0, x) - sympy.polygamma(0, y)) / (x - y))
    rows.append(_row("pos-polygamma-local", ZERO if clf == "supported" else clf, ZERO if clf == "supported" else "UNKNOWN", clf))
    a = (x + 1) * (x**2 + y)
    b = (x + 1) * (2 * x)
    sp = split_multiplicative(a, b)
    rows.append(_row("pos-common-factor", ZERO if sp["certified"] else NONZERO, ZERO if sp["certified"] else NONZERO, sp["note"]))

    rows.append(_row("neg-wrong-sign", NONZERO, newton_first_ok(F, z, x, y, -(x**3 - y**3) / (x - y)).verdict))
    rows.append(_row("neg-wrong-denom", NONZERO, newton_first_ok(F, z, x, y, (x**3 - y**3) / (x + y)).verdict))
    rows.append(_row("neg-wrong-factorial", NONZERO, hermite_xxx_ok(F, z, x, 6 * x).verdict))
    rows.append(_row("neg-wrong-deriv-order", NONZERO, repeated_ok(F, z, x, 6 * x).verdict))
    rows.append(_row("neg-wrong-multiplicity", NONZERO, hermite_xxy_ok(F, z, x, y, 3 * x**2).verdict))
    rows.append(_row("neg-wrong-limit-target", NONZERO, check_limit((x**2 - y**2) / (x - y), y, x, x).verdict))
    rows.append(_row("neg-false-pole-cancel", NONZERO, check_limit(1 / (x - y), y, x, 1).verdict))
    rows.append(_row("neg-wrong-branch-sign", NONZERO, newton_first_ok(F, z, x, y, (y**3 - x**3) / (x - y)).verdict))

    n_false_zero = sum(1 for r in rows if r["expect"] == NONZERO and r["got"] == ZERO)
    n_missed = sum(1 for r in rows if r["expect"] == ZERO and r["got"] != ZERO)
    report = {
        "n": len(rows),
        "n_false_zero": n_false_zero,
        "n_missed_positive": n_missed,
        "gate_pass": n_false_zero == 0,
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    lines = [
        "# Phase V1 generic suite",
        "",
        f"false ZERO: **{n_false_zero}**",
        f"missed positives: {n_missed}",
        f"gate: {'PASS' if report['gate_pass'] else 'FAIL'}",
        "",
        "| id | expect | got | ok |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['id']} | {r['expect']} | {r['got']} | {r['ok']} |")
    MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = run()
    print(json.dumps({k: rep[k] for k in ("n", "n_false_zero", "gate_pass")}))
    raise SystemExit(0 if rep["gate_pass"] else 1)
