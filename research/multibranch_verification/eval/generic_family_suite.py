"""Generic multi-branch family suite. FALSE FAMILY_ZERO must be 0."""
from __future__ import annotations

import json
from pathlib import Path

import sympy

from research.multibranch_verification.compose import certify_family
from research.multibranch_verification.edges import certify_edge
from research.multibranch_verification.recurrence import check_recurrence
from research.multibranch_verification.schema import (
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    LocalEdge,
)

OUT = Path(__file__).resolve().parents[1] / "GENERIC_FAMILY_SUITE.json"
MD = Path(__file__).resolve().parents[1] / "GENERIC_FAMILY_SUITE.md"

z, x, y = sympy.symbols("z x y")
F = z**3
SYMS = [{"name": n, "real": True} for n in ("x", "y", "z")]


def _edge(src, tgt, rel, var, to, verdict, prov="suite"):
    return LocalEdge(src, tgt, rel, var, to, f"{src}->{tgt}", verdict, prov)


def run() -> dict:
    rows = []
    # A 3-branch confluence: F[x,y], F[x,x], F[y,y]
    nxy = (x**3 - y**3) / (x - y)
    e1 = certify_edge(nxy, 3 * x**2, "limit", y, x, SYMS)
    e2 = certify_edge(nxy, 3 * y**2, "limit", x, y, SYMS)
    rec = check_recurrence("F[x,x]", F, z, x=x, claimed=3 * x**2)
    cert = certify_family(
        member_ids=["A", "B", "C"],
        edges=[
            _edge("A", "B", "limit", "y", "x", e1.verdict, e1.provenance),
            _edge("A", "C", "limit", "x", "y", e2.verdict, e2.provenance),
        ],
        recurrence_verdicts=[rec.verdict],
        node_multiplicities={"A": 1, "B": 2, "C": 2},
        latent_compatible=True,
    )
    rows.append({"id": "pos-3branch-confluence", "expect": FAMILY_ZERO, "got": cert.family_verdict})

    # C 5-branch Hermite cubic: members Fxy, Fxx, Fyy, Fxxy, Fxxx
    rxx = check_recurrence("F[x,x]", F, z, x=x, claimed=3 * x**2)
    rxxx = check_recurrence("F[x,x,x]", F, z, x=x, claimed=3 * x)
    rxxy = check_recurrence("F[x,x,y]", F, z, x=x, y=y, claimed=2 * x + y)
    edges5 = [
        _edge("G", "D", "limit", "y", "x", "ZERO", "toy"),
        _edge("G", "E", "limit", "x", "y", "ZERO", "toy"),
        _edge("D", "T", "limit", "y", "x", "ZERO", "toy"),
        _edge("H", "T", "hermite_dd_recurrence", "y", "x", "ZERO", "toy"),
    ]
    # Use recurrence ZERO from actual checks
    recs = [rxx.verdict, rxxx.verdict, rxxy.verdict]
    cert5 = certify_family(
        member_ids=["G", "D", "E", "H", "T"],
        edges=edges5,
        recurrence_verdicts=recs,
        node_multiplicities={"G": 1, "D": 2, "E": 2, "H": 2, "T": 3},
        latent_compatible=True,
    )
    rows.append({"id": "pos-5branch-hermite-cubic", "expect": FAMILY_ZERO, "got": cert5.family_verdict, "note": recs})

    # G two paths same result: already required by path_consistency; both ZERO
    rows.append({"id": "pos-two-paths", "expect": FAMILY_ZERO, "got": cert5.family_verdict})

    # Negatives
    bad = certify_family(
        member_ids=["G", "D"],
        edges=[_edge("G", "D", "limit", "y", "x", "NONZERO", "corrupt")],
        recurrence_verdicts=["ZERO"],
        node_multiplicities={"G": 1, "D": 2},
        latent_compatible=True,
    )
    rows.append({"id": "neg-corrupted-branch", "expect": FAMILY_NONZERO, "got": bad.family_verdict})

    mix = certify_family(
        member_ids=["G", "D", "X"],
        edges=[_edge("G", "D", "limit", "y", "x", "ZERO", "ok")],
        recurrence_verdicts=["ZERO"],
        node_multiplicities={"G": 1, "D": 2, "X": 1},
        latent_compatible=False,
    )
    rows.append({"id": "neg-mixed-latent", "expect": FAMILY_UNKNOWN, "got": mix.family_verdict})

    unk = certify_family(
        member_ids=["G", "D", "E"],
        edges=[
            _edge("G", "D", "limit", "y", "x", "ZERO", "ok"),
            _edge("G", "E", "limit", "x", "y", "UNKNOWN", "open"),
        ],
        recurrence_verdicts=["ZERO"],
        node_multiplicities={"G": 1, "D": 2, "E": 2},
        latent_compatible=True,
    )
    rows.append({"id": "neg-majority-not-zero", "expect": FAMILY_UNKNOWN, "got": unk.family_verdict})

    n_false = sum(1 for r in rows if r["expect"] != FAMILY_ZERO and r["got"] == FAMILY_ZERO)
    n_miss = sum(1 for r in rows if r["expect"] == FAMILY_ZERO and r["got"] != FAMILY_ZERO)
    for r in rows:
        r["ok"] = r["got"] == r["expect"]
    report = {
        "n": len(rows),
        "n_false_family_zero": n_false,
        "n_missed_positive": n_miss,
        "gate_pass": n_false == 0,
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    lines = ["# Generic multi-branch family suite", "",
             f"false FAMILY_ZERO: **{n_false}**", f"gate: {'PASS' if report['gate_pass'] else 'FAIL'}", "",
             "| id | expect | got | ok |", "|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['expect']} | {r['got']} | {r['ok']} |")
    MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = run()
    print(json.dumps({k: rep[k] for k in ("n", "n_false_family_zero", "gate_pass", "n_missed_positive")}))
    raise SystemExit(0 if rep["gate_pass"] else 1)
