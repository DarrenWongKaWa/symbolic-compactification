"""Generic iterated-confluence suite. FALSE FAMILY_ZERO must be 0.

Uses frozen schema composition plus Track V check_limit / spectator split.
Does not touch frozen Guo hypotheses. No LLM.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy

from research.iterated_confluence.schema import (
    CONSISTENT_ZERO,
    CONSISTENCY_UNKNOWN,
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    INCONSISTENT_NONZERO,
    PATH_NONZERO,
    PATH_UNKNOWN,
    PATH_ZERO,
    compose_family_verdict,
    compose_path_verdict,
)
from research.scalable_verification.confluence import check_limit
from research.scalable_verification.factor import split_multiplicative

OUT = Path(__file__).resolve().parents[1] / "GENERIC_SUITE.json"
MD = Path(__file__).resolve().parents[1] / "GENERIC_SUITE.md"

x, y, z = sympy.symbols("x y z")
Fcubic = z**3


def _limit(expr, var, point, target) -> str:
    return check_limit(expr, var, point, target).verdict


def _row(case_id: str, expect: str, got: str, note: str = "") -> dict[str, Any]:
    return {"id": case_id, "expect": expect, "got": got, "ok": got == expect, "note": note}


def run() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    # A. joint and iterated limits agree (cubic Newton / second derivative)
    nxy = (x**3 - y**3) / (x - y)
    e_yx = _limit(nxy, y, x, 3 * x**2)
    e_xy = _limit(nxy, x, y, 3 * y**2)
    # two paths generic -> repeated node: y->x then (already diagonal)
    p1 = compose_path_verdict([e_yx])
    p2 = compose_path_verdict([e_xy])
    fam_a = compose_family_verdict(
        path_verdicts=[p1, p2],
        consistency_verdicts=[CONSISTENT_ZERO],  # polynomial; orders agree at a point
        reconstruction_verdicts=["ZERO"],
        required_edge_verdicts=[e_yx, e_xy],
        require_path_independence=True,
    )
    rows.append(_row("A-joint-iterated-agree", FAMILY_ZERO, fam_a, f"edges {e_yx},{e_xy}"))

    # B. order of limits matters: x/(x+y)
    f = x / (x + y)
    lim_y_then_x = _limit(f, y, 0, 1)  # expect ZERO vs 1
    # after y=0, f=1, then x->0 stays 1. Direct check:
    ly = check_limit(f, y, sympy.Integer(0), sympy.Integer(1)).verdict
    lx = check_limit(f, x, sympy.Integer(0), sympy.Integer(0)).verdict
    fam_b = compose_family_verdict(
        path_verdicts=[compose_path_verdict([ly]), compose_path_verdict([lx])],
        consistency_verdicts=[INCONSISTENT_NONZERO],
        reconstruction_verdicts=["ZERO"],
        require_path_independence=True,
    )
    rows.append(_row(
        "B-order-matters",
        FAMILY_NONZERO,
        fam_b,
        f"y-then-1={ly} x-then-0={lx}; must not FAMILY_ZERO",
    ))
    assert fam_b != FAMILY_ZERO

    # C. one path valid, one invalid
    fam_c = compose_family_verdict(
        path_verdicts=[PATH_ZERO, PATH_NONZERO],
        consistency_verdicts=[INCONSISTENT_NONZERO],
        reconstruction_verdicts=["ZERO"],
        require_path_independence=True,
    )
    rows.append(_row("C-one-path-invalid", FAMILY_NONZERO, fam_c))

    # D. all pairwise edges ZERO but global family inconsistent
    fam_d = compose_family_verdict(
        path_verdicts=[PATH_ZERO, PATH_ZERO],
        consistency_verdicts=[INCONSISTENT_NONZERO],
        reconstruction_verdicts=["ZERO"],
        required_edge_verdicts=["ZERO", "ZERO", "ZERO"],
        require_path_independence=True,
    )
    rows.append(_row("D-pairwise-zero-inconsistent", FAMILY_NONZERO, fam_d))

    # E. repeated-node Hermite cubic consistent
    # F[x,x]=3x^2, F[x,x,x]=3x (F''/2! = 6x/2 = 3x)
    fxx = _limit(nxy, y, x, 3 * x**2)
    xxx_claimed = 3 * x
    # Hermite F[x,x,x] = F''(x)/2 = 3x for z^3
    rec_xx = "ZERO" if fxx == "ZERO" else fxx
    rec_xxx = "ZERO"  # checked algebraically: sympy.diff(Fcubic,z,2).subs(z,x)/2 == 3x
    assert sympy.diff(Fcubic, z, 2).subs(z, x) / 2 == xxx_claimed
    fam_e = compose_family_verdict(
        path_verdicts=[PATH_ZERO, PATH_ZERO],
        consistency_verdicts=[CONSISTENT_ZERO],
        reconstruction_verdicts=[rec_xx, rec_xxx],
        required_edge_verdicts=[fxx, "ZERO"],
        require_path_independence=True,
    )
    rows.append(_row("E-hermite-cubic-consistent", FAMILY_ZERO, fam_e, f"Fxx {fxx}"))

    # F. hidden pole: 1/(x-y) as y->x vs finite target
    pole = _limit(1 / (x - y), y, x, sympy.Integer(0))
    fam_f = compose_family_verdict(
        path_verdicts=[compose_path_verdict([pole])],
        consistency_verdicts=[CONSISTENT_ZERO],
        reconstruction_verdicts=["ZERO"],
        required_edge_verdicts=[pole],
        require_path_independence=False,
    )
    # pole vs 0 should be NONZERO (or UNKNOWN if undecided); never FAMILY_ZERO
    expect_f = FAMILY_NONZERO if pole == "NONZERO" else (
        FAMILY_UNKNOWN if pole == "UNKNOWN" else FAMILY_NONZERO
    )
    if pole == "ZERO":
        expect_f = FAMILY_ZERO  # would be a false promotion; recorded
    rows.append(_row("F-hidden-pole", expect_f if pole != "ZERO" else "FAMILY_NONZERO_or_UNKNOWN", fam_f, f"pole verdict {pole}"))
    if pole == "ZERO":
        rows[-1]["ok"] = False
        rows[-1]["expect"] = "not FAMILY_ZERO"
        rows[-1]["got"] = fam_f
    else:
        rows[-1]["expect"] = fam_f if fam_f != FAMILY_ZERO else "FAMILY_NONZERO"
        rows[-1]["ok"] = fam_f != FAMILY_ZERO
        rows[-1]["expect"] = "not FAMILY_ZERO"

    # G. spectator factoring reveals a small exact kernel
    h1 = sympy.Function("h1")
    A = h1(x) * nxy
    B = h1(x) * (3 * x**2)
    sp = split_multiplicative(A, B)
    local_v = "UNKNOWN"
    if sp["certified"]:
        local_v = _limit(sp["A_local"], y, x, sp["B_local"])
    fam_g = compose_family_verdict(
        path_verdicts=[compose_path_verdict([local_v])],
        consistency_verdicts=[],
        reconstruction_verdicts=["ZERO"] if sp["certified"] else ["UNKNOWN"],
        required_edge_verdicts=[local_v],
        require_path_independence=False,
    )
    rows.append(_row(
        "G-spectator-small-kernel",
        FAMILY_ZERO,
        fam_g,
        f"certified={sp['certified']} local={local_v} note={sp.get('note')}",
    ))

    # Two PATH_ZERO paths to the same end are not a joint-limit certificate
    # (xy/(x^2+y^2) iterated limits both 0; joint limit missing).
    fam_joint = compose_family_verdict(
        path_verdicts=[PATH_ZERO, PATH_ZERO],
        consistency_verdicts=[CONSISTENCY_UNKNOWN],
        reconstruction_verdicts=["ZERO"],
        require_path_independence=True,
    )
    rows.append(_row("neg-iterated-not-joint", FAMILY_UNKNOWN, fam_joint))

    # Majority PATH_ZERO + one UNKNOWN is not FAMILY_ZERO
    fam_maj = compose_family_verdict(
        path_verdicts=[PATH_ZERO, PATH_ZERO, PATH_UNKNOWN],
        consistency_verdicts=[CONSISTENT_ZERO],
        reconstruction_verdicts=["ZERO"],
        require_path_independence=True,
    )
    rows.append(_row("neg-majority-unknown", FAMILY_UNKNOWN, fam_maj))

    n_false = sum(1 for r in rows if r["got"] == FAMILY_ZERO and r["expect"] != FAMILY_ZERO)
    n_ok = sum(1 for r in rows if r["ok"])
    report = {
        "n": len(rows),
        "n_ok": n_ok,
        "false_FAMILY_ZERO": n_false,
        "rows": rows,
        "pass": n_false == 0 and n_ok == len(rows),
    }
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    lines = [
        "# Track V3 generic iterated-confluence suite",
        "",
        f"false FAMILY_ZERO = {n_false}",
        f"pass = {report['pass']}",
        "",
        "| id | expect | got | ok | note |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['expect']} | {r['got']} | {r['ok']} | {r['note']} |"
        )
    MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = run()
    print(json.dumps({k: rep[k] for k in ("n", "n_ok", "false_FAMILY_ZERO", "pass")}))
