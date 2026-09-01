#!/usr/bin/env python3
"""Mode A adjudication of frozen PRD-theory edges. Does not modify src/."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import sympy as sp
import yaml
from symbolic_compactification.research_api import verify_hypothesis

from edges_frozen import EDGES

ROOT = Path(__file__).resolve().parent


def parse(text: str) -> sp.Expr:
    return sp.sympify(
        text,
        locals={"Rational": sp.Rational, "I": sp.I, "pi": sp.pi, "Abs": sp.Abs},
    )


def free_names(*texts: str) -> list[str]:
    names: set[str] = set()
    for t in texts:
        if not t:
            continue
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
    symbols = [{"name": n, "real": True, "nonzero": n in {"e12", "e21", "l_Q", "mu", "sa", "ca", "q0", "kappa"}} for n in names]
    yaml.safe_dump({"symbols": symbols, "functions": []}, (dest / "assumptions" / "assumptions.yaml").open("w"))
    (dest / "project.yaml").write_text(
        "project_name: prd-theory-audit\n"
        "objective: Printed equation transition.\n"
        "expression_entrypoint: expressions/current.txt\n"
        "assumptions_file: assumptions/assumptions.yaml\n"
        "optional_notes:\n  - notes/research_notes.md\n"
        "optional_references:\n  - references/README.md\n"
    )
    (dest / "notes" / "research_notes.md").write_text("PRD theory derivation audit.\n")
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
                "obligation_id": "prd-equiv",
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
    tmp = Path(tempfile.mkdtemp(prefix="ssc-prd-"))
    try:
        write_workspace(tmp, left, right, names)
        result = verify_hypothesis(tmp)
        return {"result": str(result.result), "error_code": result.error_code, "run_id": result.run_id}
    except Exception as exc:  # noqa: BLE001
        return {"result": "ERROR", "error_code": type(exc).__name__, "detail": repr(exc)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def apply_subst(expr: str, subst: dict[str, str] | None) -> str:
    if not subst:
        return expr
    e = parse(expr)
    reps = {parse(k): parse(v) for k, v in subst.items()}
    # also allow symbol-name replacements
    sym_reps = {}
    for k, v in subst.items():
        try:
            ks = sp.Symbol(k)
            if ks in e.free_symbols:
                sym_reps[ks] = parse(v)
        except Exception:
            continue
    if sym_reps:
        e = e.subs(sym_reps)
    if reps:
        e = e.xreplace(reps)
    return str(sp.expand(e))


def final_status(edge: dict, naive: str | None, cond: str | None) -> str:
    claimed = edge["claimed"]
    if edge.get("frozen_status") == "CERTIFIED_BY_RULE":
        return "CERTIFIED_BY_RULE"
    if edge.get("frozen_status") == "UNKNOWN" and claimed == "ASYMPTOTIC":
        return "UNKNOWN_REMAINDER"
    if claimed in {"DEFINITION", "STRUCTURAL"}:
        return "STRUCTURAL"
    if claimed == "UNSUPPORTED":
        return "COMPILE_FAILURE"
    if claimed == "LIMIT_PROCEDURE":
        return "UNKNOWN"
    if edge.get("undeclared"):
        if cond == "ZERO":
            return "UNDECLARED_APPROXIMATION_REQUIRED"
        return "NONZERO"
    if claimed == "APPROXIMATION" and not edge.get("subst") and naive in {None, "N/A"}:
        return "UNKNOWN_REMAINDER"
    if naive == "ZERO" and not edge.get("subst") and claimed == "EXACT_ALGEBRA":
        return "EXACT_ZERO"
    if claimed == "SUBSTITUTION" and cond == "ZERO":
        return "ZERO_UNDER_SUBSTITUTION"
    if claimed == "APPROXIMATION" and cond == "ZERO" and not edge.get("undeclared"):
        return "CERTIFIED_UNDER_DECLARED_APPROXIMATION"
    if claimed == "APPROXIMATION" and cond == "NONZERO":
        return "NONZERO_AFTER_DECLARED_APPROXIMATION"
    if naive == "ZERO":
        return "EXACT_ZERO"
    if naive == "NONZERO" and cond == "ZERO" and claimed == "EXACT_ALGEBRA":
        return "ZERO_UNDER_SUBSTITUTION"
    if naive in {"PARSE_FAILURE", "COMPILE_FAILURE", "UNKNOWN", "ERROR"}:
        return naive if naive != "ERROR" else "PARSE_FAILURE"
    if naive == "NONZERO":
        return "NONZERO"
    return "UNKNOWN"


def mutate(expr: str, kind: str) -> str:
    if kind == "sign":
        return f"-({expr})"
    if kind == "times_two":
        return f"2*({expr})"
    if kind == "plus_one":
        return f"({expr}) + 1"
    raise ValueError(kind)


def main() -> None:
    rows = []
    controls = []
    for edge in EDGES:
        executable = edge.get("executable", True)
        naive = None
        cond_res = None
        if not executable or edge.get("left") is None:
            naive_s = "N/A"
            cond_s = "N/A"
        else:
            naive = verify_pair(edge["left"], edge["right"])
            naive_s = naive["result"]
            if edge.get("undeclared") and "T_A_right" in edge:
                cond_res = verify_pair(edge["left"], edge["T_A_right"])
                cond_s = cond_res["result"]
            elif edge.get("subst"):
                l2 = apply_subst(edge["left"], edge["subst"])
                r2 = apply_subst(edge.get("extra_right") or edge["right"], edge["subst"])
                cond_res = verify_pair(l2, r2)
                cond_s = cond_res["result"]
            else:
                cond_s = "N/A"
        status = final_status(edge, None if naive_s == "N/A" else naive_s, None if cond_s == "N/A" else cond_s)
        if edge.get("frozen_status") == "CERTIFIED_BY_RULE":
            cond_s = "local child ZERO"
        if edge.get("frozen_status") == "UNKNOWN":
            cond_s = "UNKNOWN"
        row = {
            "id": edge["id"],
            "paper": edge["paper"],
            "eq": edge["eq"],
            "move": edge["move"],
            "claimed": edge["claimed"],
            "direct": naive_s,
            "condition": edge.get("cond") or "none",
            "conditional": cond_s,
            "final": status,
            "note": edge.get("note"),
        }
        rows.append(row)
        print(edge["id"], naive_s, cond_s, status, flush=True)

        if executable and edge.get("left") and naive_s == "ZERO" and not edge.get("undeclared"):
            for kind in ("sign", "times_two", "plus_one"):
                m = verify_pair(edge["left"], mutate(edge["right"], kind))
                controls.append({
                    "id": f"{edge['id']}-neg-{kind}",
                    "parent": edge["id"],
                    "kind": kind,
                    "result": m["result"],
                    "false_promotion": m["result"] == "ZERO",
                })

    n_false = sum(1 for c in controls if c["false_promotion"])
    (ROOT / "metrics").mkdir(exist_ok=True)
    payload = {"rows": rows, "controls": controls, "false_promotions": n_false, "n_controls": len(controls)}
    (ROOT / "metrics" / "records.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("n_rows", len(rows), "controls", len(controls), "false_promo", n_false)


if __name__ == "__main__":
    main()
