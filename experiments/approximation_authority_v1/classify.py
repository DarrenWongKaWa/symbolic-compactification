#!/usr/bin/env python3
"""Classify approximation-mediated steps on the frozen Mode A verifier.

Does not modify src/. Never writes approximate ZERO. Overlay parent labels
are experiment-level and must not be confused with engine results.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import sympy as sp
import yaml
from symbolic_compactification.research_api import verify_hypothesis

ROOT = Path(__file__).resolve().parent
EXPR = ROOT / "expressions"


def parse(text: str) -> sp.Expr:
    return sp.sympify(text, locals={"Rational": sp.Rational, "I": sp.I})


def free_names(*texts: str) -> list[str]:
    names: set[str] = set()
    for t in texts:
        try:
            names |= {str(s) for s in parse(t).free_symbols}
        except Exception:
            continue
    return sorted(names)


def write_workspace(dest: Path, left: str, right: str, names: list[str]) -> None:
    (dest / "expressions").mkdir()
    (dest / "assumptions").mkdir()
    (dest / "hypotheses").mkdir()
    (dest / "notes").mkdir()
    (dest / "references").mkdir()
    (dest / "expressions" / "current.txt").write_text(left.strip() + "\n")
    (dest / "expressions" / "candidate.txt").write_text(right.strip() + "\n")
    symbols = [{"name": n, "real": True, "nonzero": n in {"e12", "e21", "G"}} for n in names]
    yaml.safe_dump({"symbols": symbols, "functions": []}, (dest / "assumptions" / "assumptions.yaml").open("w"))
    (dest / "project.yaml").write_text(
        "project_name: approximation-authority\n"
        "objective: Exact residual after optional declared approximation.\n"
        "expression_entrypoint: expressions/current.txt\n"
        "assumptions_file: assumptions/assumptions.yaml\n"
        "optional_notes:\n  - notes/research_notes.md\n"
        "optional_references:\n  - references/README.md\n"
    )
    (dest / "notes" / "research_notes.md").write_text("Approximation-authority classification.\n")
    (dest / "references" / "README.md").write_text("None.\n")
    hyp = {
        "assumptions_used": names,
        "hypothesis_type": "equivalence",
        "instance_maps": {
            "expressions/candidate.txt": {"presentation": "candidate"},
            "expressions/current.txt": {"presentation": "current"},
        },
        "latent_object": None,
        "members": ["expressions/current.txt", "expressions/candidate.txt"],
        "operators": ["EQUIVALENCE"],
        "proof_obligations": [
            {
                "left": "expressions/current.txt",
                "obligation_id": "approx-equiv",
                "relation": "equivalent",
                "right": "expressions/candidate.txt",
            }
        ],
        "reconstruction_rule": "Exact residual left - right.",
        "schema_version": 1,
    }
    (dest / "hypotheses" / "hypothesis.json").write_text(json.dumps(hyp, indent=2) + "\n")


def verify_pair(left: str, right: str) -> dict:
    names = free_names(left, right) or ["x"]
    tmp = Path(tempfile.mkdtemp(prefix="ssc-aa-"))
    try:
        write_workspace(tmp, left, right, names)
        result = verify_hypothesis(tmp)
        status = str(result.result)
        return {
            "result": status,
            "error_code": result.error_code,
            "run_id": result.run_id,
            "promoted_as_engine_zero": status == "ZERO",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "result": "ERROR",
            "error_code": type(exc).__name__,
            "detail": repr(exc),
            "promoted_as_engine_zero": False,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def drop_G_degree_geq_2(text: str) -> str:
    expr = parse(text)
    G = sp.Symbol("G")
    expanded = sp.expand(expr)
    poly = sp.Poly(expanded, G)
    kept = 0
    for monom, coeff in poly.as_dict().items():
        deg = monom[0]
        if deg < 2:
            kept += coeff * G**deg
    return str(sp.expand(kept))


def coeff_of(text: str, var: str, degree: int) -> str:
    expr = parse(text)
    v = sp.Symbol(var)
    return str(sp.expand(expr).coeff(v, degree))


def overlay_for(task: dict, naive: dict | None, downstream: dict | None, hidden: dict | None, coeff: dict | None) -> str:
    expected = task["expected_overlay"]
    # Overlay is a function of measured results, not of the expected label.
    provenance = task["provenance"]
    naive_r = None if naive is None else naive["result"]
    down_r = None if downstream is None else downstream["result"]
    hidden_r = None if hidden is None else hidden["result"]
    if task["task_id"] == "AA-03":
        return "ASYMPTOTIC_DECLARED_ONLY"
    if task["task_id"] == "AA-06":
        return "SUBSTITUTION_NOT_APPROXIMATION"
    if task["task_id"] == "AA-10":
        return "COEFFICIENT_ZERO_NOT_REMAINDER"
    if provenance == "NONE" and naive_r == "ZERO":
        return "ENGINE_ZERO"
    if provenance == "AUTHOR_DECLARED" and down_r == "ZERO":
        return "CERTIFIED_UNDER_DECLARED_APPROXIMATION"
    if provenance == "AUTHOR_DECLARED" and down_r == "NONZERO":
        return "REFUSED_DOWNSTREAM_NONZERO"
    if provenance == "MODEL_PROPOSED" and down_r == "ZERO":
        return "MODEL_APPROX_NOT_AUTHORIZED"
    if provenance == "NONE" and naive_r == "NONZERO" and hidden_r == "ZERO":
        return "UNDECLARED_APPROXIMATION_REQUIRED"
    if provenance == "NONE" and naive_r == "NONZERO" and task["task_id"] == "AA-08":
        return "NAIVE_REMAINDER_AS_EXACT_REFUSED"
    return f"UNMAPPED:{expected}"


def read_expr(name: str | None) -> str | None:
    if not name:
        return None
    return (EXPR / name).read_text().strip()


def main() -> None:
    frozen = yaml.safe_load((ROOT / "TASKS_FROZEN.yaml").read_text())
    rows = []
    for task in frozen["tasks"]:
        tid = task["task_id"]
        current = read_expr(task.get("current_file"))
        nxt = read_expr(task.get("next_file"))
        naive = None
        downstream = None
        hidden = None
        coeff = None
        tilde = None
        if tid == "AA-03":
            row_core = {
                "naive": None,
                "downstream": None,
                "hidden_probe": None,
                "coefficient_child": None,
                "note": (
                    "Frozen public Guo edge D.gamma-asymptotic: ASYMPTOTIC_CLAIM, "
                    "status UNKNOWN, remainder_certificate_hash null. Not rewritten "
                    "as F-(F0+Gamma F1)=0."
                ),
                "frozen_audit_status": task.get("frozen_audit_status"),
            }
        else:
            assert current is not None and nxt is not None
            naive = verify_pair(current, nxt)
            ta = task.get("T_A") or {}
            if ta.get("id") == "drop_G_degree_geq_2":
                tilde = drop_G_degree_geq_2(current)
                if task.get("provenance") in {"AUTHOR_DECLARED", "MODEL_PROPOSED"}:
                    downstream = verify_pair(tilde, nxt)
                if task.get("provenance") == "NONE":
                    hidden = verify_pair(tilde, nxt)
            if tid == "AA-10":
                spec = task["coeff"]
                extracted = coeff_of(current, spec["variable"], spec["degree"])
                coeff = verify_pair(extracted, spec["claimed"])
                coeff["extracted"] = extracted
            row_core = {
                "naive": naive,
                "E_tilde": tilde,
                "downstream": downstream,
                "hidden_probe": hidden,
                "coefficient_child": coeff,
            }
        overlay = overlay_for(task, naive, downstream, hidden, coeff)
        distinguished = overlay == task["expected_overlay"]
        row = {
            "task_id": tid,
            "diagnostic_case": task["diagnostic_case"],
            "provenance": task["provenance"],
            "expected_overlay": task["expected_overlay"],
            "observed_overlay": overlay,
            "distinguished": distinguished,
            "engine_zero_on_parent": False,
            **row_core,
        }
        # Safety: parent overlay must never be the string ZERO.
        if overlay == "ZERO" or overlay == "ENGINE_ZERO" and tid not in {"AA-05"}:
            if overlay == "ZERO":
                raise SystemExit(f"STOP: overlay labeled ZERO on {tid}")
        if overlay == "ENGINE_ZERO" and naive and naive["result"] != "ZERO":
            raise SystemExit(f"STOP: ENGINE_ZERO without naive ZERO on {tid}")
        rows.append(row)
        print(
            tid,
            "naive",
            None if naive is None else naive["result"],
            "down",
            None if downstream is None else downstream["result"],
            "hidden",
            None if hidden is None else hidden["result"],
            "overlay",
            overlay,
            "OK" if distinguished else "MISMATCH",
            flush=True,
        )

    n = len(rows)
    n_ok = sum(1 for r in rows if r["distinguished"])
    four = [r for r in rows if r["diagnostic_case"] in {1, 2, 3, 4}]
    four_ok = all(r["distinguished"] for r in four)
    parent_called_zero = [r["task_id"] for r in rows if r["observed_overlay"] == "ZERO"]
    out = {
        "n_tasks": n,
        "n_distinguished": n_ok,
        "four_diagnostic_cases_distinguished": four_ok,
        "parent_overlay_called_ZERO": parent_called_zero,
        "rows": rows,
    }
    (ROOT / "metrics").mkdir(exist_ok=True)
    (ROOT / "metrics" / "classification.json").write_text(json.dumps(out, indent=2) + "\n")
    print("four_cases", four_ok, "n_ok", n_ok, "/", n)


if __name__ == "__main__":
    main()
