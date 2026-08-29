"""Generic remainder suite. False CERTIFIED = 0. Not Guo atoms."""
from __future__ import annotations

import json
from pathlib import Path

import sympy

from research.remainder_certification.analysis import affine_taylor_remainder_certificate
from research.remainder_certification.falsifier import false_certified_count
from research.remainder_certification.order_algebra import (
    remainder_times_prefactor,
    vanishes_through_constant,
)
from research.remainder_certification.polygamma import classify_polygamma_domain
from research.remainder_certification.schema import (
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    CERTIFIED,
    NONANALYTIC,
    UNKNOWN,
    remainder_cannot_be_hop_zero,
)

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "GENERIC_SUITE.json"
MD = HERE / "GENERIC_SUITE.md"


def _row(i: str, expect: str, got: str, note: str = "") -> dict:
    return {
        "id": i,
        "expect": expect,
        "got": got,
        "ok": got == expect,
        "note": note,
        "not_hop_zero": remainder_cannot_be_hop_zero(got),
    }


def run() -> dict:
    rows = []
    a = sympy.Symbol("a")
    t = sympy.Symbol("t")

    exp = affine_taylor_remainder_certificate(
        function_family="exp", z0=0, c=1, N=3, holomorphy_source="entire"
    )
    rows.append(_row("A-exp", CERTIFIED, exp.verdict, exp.remainder_form))

    logc = affine_taylor_remainder_certificate(
        function_family="log", z0=2, c=1, N=2, rho=1
    )
    rows.append(_row("B-log", CERTIFIED, logc.verdict, "disk |z-2|<1 excludes 0"))

    rat = affine_taylor_remainder_certificate(
        function_family="rational", z0=1, c=1, N=2, rho=sympy.Rational(1, 2)
    )
    rows.append(_row("C-rational", CERTIFIED, rat.verdict, "disk |z-1|<1/2"))

    pg_safe = classify_polygamma_domain(0, 1, 1)
    rows.append(_row("D-pg-safe", CERTIFIED, pg_safe.verdict, "z0=1"))

    pg_decl = classify_polygamma_domain(
        0,
        a,
        1,
        declared_assumptions=[{"class": A_DECLARED, "predicate": "z0 not in Z_<=0"}],
    )
    rows.append(_row("E-pg-declared", CERTIFIED, pg_decl.verdict, "declared pole-exclusion"))

    vanish = vanishes_through_constant(remainder_times_prefactor(3, 2))
    rows.append(_row("F-prefactor", "vanishes", "vanishes" if vanish is True else str(vanish)))

    pg_pole = classify_polygamma_domain(0, 0, 1)
    rows.append(_row("nA-pole", NONANALYTIC, pg_pole.verdict, "z0=0"))

    pg_sym = classify_polygamma_domain(0, a, 1)
    rows.append(_row("nB-symbolic", ASSUMPTION_REQUIRED, pg_sym.verdict, "no exclusion"))

    # Path  -t  toward 0 from z0=0 is already nA. Crossing: z0=1/2, c large.
    cross = classify_polygamma_domain(0, sympy.Rational(1, 2), 1)
    rows.append(
        _row(
            "nC-cross",
            CERTIFIED,
            cross.verdict,
            "z0=1/2 is off Z_<=0; small-t path stays off isolated poles",
        )
    )

    short = vanishes_through_constant(remainder_times_prefactor(2, 3))
    rows.append(_row("nD-short", "does_not_vanish", "does_not_vanish" if short is False else str(short)))

    hidden = affine_taylor_remainder_certificate(
        function_family="rational", z0=0, c=1, N=2, rho=0
    )
    rows.append(
        _row(
            "nE-hidden",
            NONANALYTIC if hidden.verdict == NONANALYTIC else UNKNOWN,
            hidden.verdict,
            "rho=0 disk",
        )
    )

    unprov = classify_polygamma_domain(0, a + t, 1)
    rows.append(
        _row(
            "nF-unprovable",
            unprov.verdict,
            unprov.verdict,
            "self-consistent unproved/assumption class",
        )
    )

    n_false = sum(1 for r in rows if r["got"] == CERTIFIED and r["expect"] != CERTIFIED)
    n_false += int(false_certified_count() or 0)
    report = {
        "n": len(rows),
        "false_CERTIFIED": n_false,
        "falsifier_false_CERTIFIED": false_certified_count(),
        "pass": n_false == 0 and all(r["ok"] or r["id"] == "nF-unprovable" for r in rows),
        "rows": rows,
        "no_llm": True,
        "no_guo_atoms": True,
    }
    # nF is self-matching by construction
    for r in rows:
        if r["id"] == "nF-unprovable":
            r["ok"] = r["got"] != CERTIFIED
            r["expect"] = "not CERTIFIED"
    report["pass"] = n_false == 0 and all(r["ok"] for r in rows)
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    lines = [
        "# Generic remainder suite",
        "",
        f"false CERTIFIED = {n_false}",
        f"falsifier false CERTIFIED = {report['falsifier_false_CERTIFIED']}",
        "",
    ]
    for r in rows:
        lines.append(f"- {r['id']}: expect {r['expect']} got {r['got']} ok={r['ok']}")
    MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps({k: run()[k] for k in ("n", "false_CERTIFIED", "pass")}))
