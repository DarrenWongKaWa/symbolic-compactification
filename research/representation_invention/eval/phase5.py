"""Generic DD validation before any new Guo LLM calls.

Required positives must be ZERO (or documented unsupported).
Required negatives must not be ZERO.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.representation_invention.obligations import (
    COMPILE_OK,
    ZERO,
    compile_hypothesis,
    verify_obligation,
)
from research.representation_invention.schema import (
    NodeSpec,
    ObligationDraft,
    OperatorSpec,
    RepresentationHypothesisV2,
)

ROOT = Path(__file__).resolve().parents[3]
OUT_JSON = Path(__file__).resolve().parents[1] / "RESULTS_PHASE5.json"
OUT_MD = Path(__file__).resolve().parents[1] / "RESULTS_PHASE5.md"

SYMS = [{"name": n, "real": True} for n in ("x", "y", "z", "w")]
FNS = ["polygamma"]


def _hyp(**kw) -> RepresentationHypothesisV2:
    base = dict(
        representation_type="divided_difference",
        member_ids=["G0001"],
        member_roles={"G0001": "generic"},
        latent_object="F(z) = z**3",
        latent_variables=["z"],
        nodes=[NodeSpec("x", "x", 1), NodeSpec("y", "y", 1)],
        operators=[OperatorSpec("G0001", "newton_dd", {"nodes": ["x", "y"]})],
        instance_maps={"G0001": {"nodes": ["x", "y"]}},
        reconstruction_rule="(F(x)-F(y))/(x-y)",
        required_assumptions=["Ne(x, y)"],
        proof_obligations=[
            ObligationDraft(
                kind="NEWTON_DD",
                member_ids=["G0001"],
                operator="newton_dd",
                expected="equal",
            )
        ],
        scientific_rationale="phase5",
        confidence=1.0,
        parse_status="OK",
    )
    base.update(kw)
    return RepresentationHypothesisV2(**base)


def _run(h, catalog, functions=None) -> dict[str, Any]:
    cr = compile_hypothesis(h, catalog, SYMS, functions or [])
    vs = [verify_obligation(o, symbols=SYMS, functions=functions or []) for o in cr.obligations]
    verdicts = [v.verdict for v in vs]
    return {
        "compile_status": cr.compile_status,
        "n_ok": cr.n_ok,
        "n_fail": cr.n_fail,
        "notes": list(cr.notes),
        "verdicts": verdicts,
        "details": [v.to_dict() for v in vs],
    }


def cases() -> list[dict[str, Any]]:
    z2 = "(x**2 - y**2)/(x - y)"
    z3 = "(x**3 - y**3)/(x - y)"
    return [
        {
            "id": "pos-newton-z2",
            "expect": "ZERO",
            "result": _run(
                _hyp(latent_object="F(z) = z**2"),
                {"G0001": z2},
            ),
        },
        {
            "id": "pos-newton-z3",
            "expect": "ZERO",
            "result": _run(_hyp(), {"G0001": z3}),
        },
        {
            "id": "pos-repeated-diagonal",
            "expect": "ZERO",
            "result": _run(
                _hyp(
                    representation_type="hermite_divided_difference",
                    latent_object="F(z) = z**2",
                    nodes=[NodeSpec("x", "x", 2)],
                    operators=[OperatorSpec("G0001", "hermite_dd", {"nodes": ["x", "x"]})],
                    instance_maps={"G0001": {"nodes": ["x", "x"]}},
                    reconstruction_rule="F[x,x]=F'(x)",
                    proof_obligations=[
                        ObligationDraft(
                            kind="HERMITE_DD",
                            member_ids=["G0001"],
                            operator="hermite_dd",
                            expected="equal",
                        )
                    ],
                ),
                {"G0001": "2*x"},
            ),
        },
        {
            "id": "pos-hermite-xxy",
            "expect": "ZERO",
            "result": _run(
                _hyp(
                    representation_type="hermite_divided_difference",
                    nodes=[NodeSpec("x", "x", 2), NodeSpec("y", "y", 1)],
                    operators=[OperatorSpec("G0001", "hermite_dd", {"nodes": ["x", "x", "y"]})],
                    instance_maps={"G0001": {"nodes": ["x", "x", "y"]}},
                    reconstruction_rule="F[x,x,y]",
                    proof_obligations=[
                        ObligationDraft(
                            kind="HERMITE_DD",
                            member_ids=["G0001"],
                            operator="hermite_dd",
                            expected="equal",
                        )
                    ],
                ),
                {"G0001": "2*x + y"},
            ),
        },
        {
            "id": "pos-hermite-xxx",
            "expect": "ZERO",
            "result": _run(
                _hyp(
                    representation_type="hermite_divided_difference",
                    nodes=[NodeSpec("x", "x", 3)],
                    operators=[OperatorSpec("G0001", "hermite_dd", {"nodes": ["x", "x", "x"]})],
                    instance_maps={"G0001": {"nodes": ["x", "x", "x"]}},
                    reconstruction_rule="F[x,x,x]=F''(x)/2",
                    proof_obligations=[
                        ObligationDraft(
                            kind="HERMITE_DD",
                            member_ids=["G0001"],
                            operator="hermite_dd",
                            expected="equal",
                        )
                    ],
                ),
                {"G0001": "3*x"},
            ),
        },
        {
            "id": "pos-piecewise-confluence",
            "expect": "ZERO",
            "result": _run(
                _hyp(
                    representation_type="local_confluence",
                    member_ids=["G0001", "G0002"],
                    member_roles={"G0001": "generic", "G0002": "degenerate"},
                    latent_object="F(z) = z**2",
                    operators=[OperatorSpec("G0001", "limit", {"var": "x", "to": "y"})],
                    instance_maps={},
                    reconstruction_rule="limit generic -> degenerate",
                    proof_obligations=[
                        ObligationDraft(
                            kind="CONFLUENCE",
                            member_ids=["G0001", "G0002"],
                            operator="limit",
                            expected="equal",
                            variables={"var": "x", "to": "y"},
                        )
                    ],
                ),
                {"G0001": "(x**2 - y**2)/(x - y)", "G0002": "2*y"},
            ),
        },
        {
            "id": "pos-polygamma-newton",
            "expect": "ZERO",
            "result": _run(
                _hyp(
                    latent_object="F(z) = polygamma(0, z)",
                    reconstruction_rule="(psi(x)-psi(y))/(x-y)",
                ),
                {"G0001": "(polygamma(0, x) - polygamma(0, y))/(x - y)"},
                functions=FNS,
            ),
        },
        {
            "id": "neg-wrong-sign",
            "expect": "NONZERO",
            "result": _run(_hyp(), {"G0001": "-(x**3 - y**3)/(x - y)"}),
        },
        {
            "id": "neg-wrong-denominator",
            "expect": "NONZERO",
            "result": _run(_hyp(), {"G0001": "(x**3 - y**3)/(x + y)"}),
        },
        {
            "id": "neg-wrong-derivative-order",
            "expect": "NONZERO",
            "result": _run(
                _hyp(
                    representation_type="hermite_divided_difference",
                    nodes=[NodeSpec("x", "x", 2)],
                    operators=[OperatorSpec("G0001", "hermite_dd", {"nodes": ["x", "x"]})],
                    instance_maps={"G0001": {"nodes": ["x", "x"]}},
                    proof_obligations=[
                        ObligationDraft(
                            kind="HERMITE_DD",
                            member_ids=["G0001"],
                            operator="hermite_dd",
                            expected="equal",
                        )
                    ],
                ),
                {"G0001": "6*x"},
            ),
        },
        {
            "id": "neg-wrong-repeated-as-first-dd",
            "expect": "NONZERO",
            "result": _run(_hyp(), {"G0001": "3*x**2"}),
        },
        {
            "id": "neg-swapped-limit",
            "expect": "NONZERO",
            "result": _run(
                _hyp(
                    representation_type="local_confluence",
                    member_ids=["G0001", "G0002"],
                    member_roles={"G0001": "generic", "G0002": "degenerate"},
                    operators=[OperatorSpec("G0001", "limit", {"var": "x", "to": "y"})],
                    proof_obligations=[
                        ObligationDraft(
                            kind="CONFLUENCE",
                            member_ids=["G0001", "G0002"],
                            operator="limit",
                            expected="equal",
                            variables={"var": "x", "to": "y"},
                        )
                    ],
                ),
                {"G0001": "(x**2 - y**2)/(x - y)", "G0002": "x + y"},
            ),
        },
    ]


def evaluate() -> dict[str, Any]:
    rows = []
    n_false_zero = 0
    n_missed_pos = 0
    unsupported = []
    for case in cases():
        r = case["result"]
        expect = case["expect"]
        verdicts = [v for v in r["verdicts"] if v]
        primary = verdicts[0] if verdicts else (
            "COMPILE_FAILURE" if r["compile_status"] != COMPILE_OK else "UNKNOWN"
        )
        ok = False
        if expect == "ZERO":
            ok = primary == ZERO
            if not ok:
                n_missed_pos += 1
                if primary != ZERO:
                    unsupported.append({"id": case["id"], "got": primary})
        else:
            ok = primary != ZERO
            if primary == ZERO:
                n_false_zero += 1
        rows.append({
            "id": case["id"],
            "expect": expect,
            "got": primary,
            "ok": ok,
            "compile_status": r["compile_status"],
            "notes": r["notes"],
        })
    gate = n_false_zero == 0
    return {
        "n_cases": len(rows),
        "n_false_zero": n_false_zero,
        "n_missed_positive": n_missed_pos,
        "gate_pass": gate,
        "unsupported": unsupported,
        "rows": rows,
    }


def write_reports(report: dict[str, Any] | None = None) -> dict[str, Any]:
    report = report or evaluate()
    OUT_JSON.write_text(json.dumps(report, indent=2))
    lines = [
        "# Phase 5 — generic DD validation",
        "",
        f"false ZERO: **{report['n_false_zero']}**",
        f"missed positives: {report['n_missed_positive']}",
        f"gate: {'PASS' if report['gate_pass'] else 'FAIL'}",
        "",
        "| id | expect | got | ok |",
        "|---|---|---|---|",
    ]
    for r in report["rows"]:
        lines.append(f"| {r['id']} | {r['expect']} | {r['got']} | {r['ok']} |")
    if report["unsupported"]:
        lines += ["", "## Documented unsupported / missed positives", ""]
        for u in report["unsupported"]:
            lines.append(f"- `{u['id']}` got `{u['got']}`")
    OUT_MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = write_reports()
    print(json.dumps({k: rep[k] for k in ("n_cases", "n_false_zero", "gate_pass")}, indent=2))
    raise SystemExit(0 if rep["gate_pass"] else 1)
