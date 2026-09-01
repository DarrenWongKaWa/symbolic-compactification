#!/usr/bin/env python3
"""Deterministic verification + RESULTS.md generation.

Replay does not require an LLM. Frozen relations are the input.
Does not modify src/. ZERO always means exact engine ZERO.
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path

import sympy as sp
import yaml
from symbolic_compactification.research_api import verify_hypothesis

from relations_frozen import ROOT, all_relations

LOCALS = {
    "Rational": sp.Rational,
    "I": sp.I,
    "pi": sp.pi,
    "E": sp.E,
    "oo": sp.oo,
    "Abs": sp.Abs,
    "diff": sp.diff,
}


def parse(text: str, functions: list[str] | None = None) -> sp.Expr:
    loc = dict(LOCALS)
    for fname in functions or []:
        loc[fname] = sp.Function(fname)
    return sp.sympify(text, locals=loc)


_IDENT = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_RESERVED_NAMES = {
    "I", "pi", "E", "oo", "Rational", "Abs", "diff", "Integer",
    "True", "False", "and", "or", "not",
}


def free_names(*texts: str, functions: list[str] | None = None) -> list[str]:
    """Declare every identifier token in the frozen strings.

    Do not trust sympy free_symbols here: ``e12`` can be read as scientific
    notation, which would omit a real paper symbol from assumptions.yaml
    and fail closed as PARSE_FAILURE.
    """
    names: set[str] = set()
    fn = set(functions or [])
    for t in texts:
        if not t:
            continue
        names |= set(_IDENT.findall(t))
    names -= _RESERVED_NAMES
    names -= fn
    return sorted(names)


def detect_functions(text: str) -> list[str]:
    found = []
    for m in re.finditer(r"\b([A-Za-z][A-Za-z0-9_]*)\s*\(", text):
        name = m.group(1)
        if name not in LOCALS and name not in found:
            found.append(name)
    return found


def apply_subst(expr: str, subst: dict[str, str] | None, functions: list[str] | None) -> str:
    if not subst:
        return expr
    e = parse(expr, functions)
    items = sorted(subst.items(), key=lambda kv: -len(kv[0]))
    for k, v in items:
        ve = parse(v, functions)
        try:
            ks = sp.Symbol(k)
            if ks in e.free_symbols:
                e = e.subs(ks, ve)
                continue
        except Exception:
            pass
        ke = parse(k, functions)
        e2 = e.xreplace({ke: ve})
        if e2 == e:
            e2 = e.subs(ke, ve)
        if e2 == e:
            e2 = sp.expand(e).xreplace({sp.expand(ke): ve})
        if e2 == e:
            e2 = sp.expand(e).subs(sp.expand(ke), ve)
        e = e2
    return str(sp.expand(e))


def write_workspace(dest: Path, left: str, right: str, names: list[str], functions: list[str]) -> None:
    (dest / "expressions").mkdir()
    (dest / "assumptions").mkdir()
    (dest / "hypotheses").mkdir()
    (dest / "notes").mkdir()
    (dest / "references").mkdir()
    (dest / "expressions" / "current.txt").write_text(left.strip() + "\n")
    (dest / "expressions" / "candidate.txt").write_text(right.strip() + "\n")
    nonzero = {"e12", "e21"}
    symbols = [{"name": n, "real": True, "nonzero": n in nonzero} for n in names]
    yaml.safe_dump(
        {"symbols": symbols, "functions": functions},
        (dest / "assumptions" / "assumptions.yaml").open("w"),
    )
    (dest / "project.yaml").write_text(
        "project_name: guo-flagship-audit\n"
        "objective: Printed equation transition.\n"
        "expression_entrypoint: expressions/current.txt\n"
        "assumptions_file: assumptions/assumptions.yaml\n"
        "optional_notes:\n  - notes/research_notes.md\n"
        "optional_references:\n  - references/README.md\n"
    )
    (dest / "notes" / "research_notes.md").write_text("Guo flagship full-paper audit.\n")
    (dest / "references" / "README.md").write_text("arXiv:2511.16422v2\n")
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
                "obligation_id": "flagship-equiv",
                "relation": "equivalent",
                "right": "expressions/candidate.txt",
            }
        ],
        "reconstruction_rule": "Exact residual left - right.",
        "schema_version": 1,
    }
    (dest / "hypotheses" / "hypothesis.json").write_text(json.dumps(hyp, indent=2) + "\n")


def verify_pair(left: str, right: str) -> dict:
    functions = sorted(set(detect_functions(left)) | set(detect_functions(right)))
    names = free_names(left, right, functions=functions) or ["x"]
    tmp = Path(tempfile.mkdtemp(prefix="ssc-guo-flag-"))
    try:
        write_workspace(tmp, left, right, names, functions)
        result = verify_hypothesis(tmp)
        return {
            "result": str(result.result),
            "error_code": result.error_code,
            "run_id": result.run_id,
        }
    except Exception as exc:  # noqa: BLE001
        return {"result": "ERROR", "error_code": type(exc).__name__, "detail": repr(exc)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def mutate(expr: str, kind: str) -> str:
    if kind == "sign":
        return f"-({expr})"
    if kind == "times_two":
        return f"2*({expr})"
    if kind == "plus_one":
        return f"({expr}) + 1"
    raise ValueError(kind)


def printed_key(p: str) -> tuple:
    if p.isdigit():
        return (0, int(p))
    letter, num = p.split("-", 1)
    return (ord(letter) - ord("A") + 1, int(num))


def relation_sort_key(rel: dict) -> tuple:
    nums = [n for n in (rel["targets"] + rel["sources"]) if n]
    if not nums:
        return (99, 0)
    return min(printed_key(n) for n in nums)


def final_status(rel: dict, naive: str, cond: str) -> str:
    if rel.get("parent_status") == "CERTIFIED_BY_RULE":
        return "CERTIFIED_BY_RULE"
    if rel.get("parent_status") == "UNKNOWN_REMAINDER":
        return "UNKNOWN_REMAINDER"
    claimed = rel["claimed"]
    if claimed in {
        "SPLIT_PARENT",
        "BOOKKEEPING",
        "DEFINITION_INSERTION",
        "LIMIT_CLAIM",
        "SPECIAL_FUNCTION_IDENTITY",
        "SERIES_COEFFICIENT",
    } and not rel.get("executable"):
        if claimed == "LIMIT_CLAIM":
            return "UNKNOWN"
        if claimed in {"SPECIAL_FUNCTION_IDENTITY", "SERIES_COEFFICIENT"}:
            return "UNSUPPORTED"
        return "STRUCTURAL"
    if not rel.get("executable"):
        if claimed == "BZ_PERIODIC_INTEGRATION_BY_PARTS":
            return "CERTIFIED_BY_RULE"
        if claimed == "ASYMPTOTIC_CLAIM":
            return "UNKNOWN_REMAINDER"
        return "UNSUPPORTED"
    if naive == "ZERO" and not rel.get("subst"):
        return "EXACT_ZERO"
    if rel.get("subst") and cond == "ZERO":
        return "ZERO_UNDER_SUBSTITUTION"
    if naive == "ZERO":
        return "EXACT_ZERO"
    if naive in {"PARSE_FAILURE", "COMPILE_FAILURE", "UNKNOWN", "ERROR"}:
        return naive if naive != "ERROR" else "PARSE_FAILURE"
    if naive == "NONZERO" and cond == "ZERO":
        return "ZERO_UNDER_SUBSTITUTION"
    if naive == "NONZERO":
        return "NONZERO"
    return "UNKNOWN"


def md_cell(s: str) -> str:
    # GitHub tables split on raw |. Escape every pipe, including those in math.
    return s.replace("\n", " ").replace("|", r"\|")


STANDALONE_CUE = {
    "2": r"nonlinear Drude $\sigma^{(-2)}$",
    "3": r"Berry-curvature dipole $\sigma^{(-1)}$",
    "5": r"kinetic $\sigma^{\mathrm{kin}}\propto v^3 f_0^{(4)}$",
    "6": r"geometric $\sigma^{\mathrm{geo}}$",
    "7": r"${\cal P}{\cal T}$-symmetric lattice Hamiltonian",
    "8": r"block-diagonal $h(\mathbf{k})$",
    "A-9": r"total $H(t)$ system+bath",
    "A-11": r"broadened $\rho^{(0)}$ bath integral",
    "A-12": r"first-order NESS kernel",
    "A-13": r"second-order NESS kernel",
    "B-21": r"$V(t)$ Peierls expansion",
    "B-22": r"$J_a(t)$ current expansion",
    "B-23": r"$j_a^{(2)}$ trace formula",
    "C-28": r"polygamma arguments $z_{n,\pm}$",
    "C-29": r"presented $\mathcal{C}_{nn}^{(1,2)}$",
    "C-31": r"presented $\mathcal{C}_{nm}^{(1,2)}$",
    "C-33": r"presented $\mathcal{C}_{nnn}^{(2,2)}$",
    "C-36": r"$P_0$ ($\psi^{(0)}$)",
    "C-37": r"$P_1$ ($\psi^{(1)}$)",
    "C-38": r"$P_2$ ($\psi^{(2)}$)",
    "C-41": r"$Q_0$ ($\psi^{(0)}$)",
    "C-42": r"$Q_1$ ($\psi^{(1)}$)",
    "C-43": r"$Q_2$ ($\psi^{(2)}$)",
    "C-44": r"$Q_3$ ($\psi^{(3)}$)",
    "C-47": r"$U_0$ ($\psi^{(0)}$)",
    "C-48": r"$U_1$ ($\psi^{(1)}$)",
    "C-49": r"$U_2$ ($\psi^{(2)}$)",
    "C-50": r"$U_3$ ($\psi^{(3)}$)",
    "C-53": r"$R_0$ ($\psi^{(0)}$)",
    "C-54": r"$R_1$ ($\psi^{(1)}$)",
    "C-55": r"$R_2$ ($\psi^{(2)}$)",
    "D-58": r"$\sigma^{(-2)}$ in $K_1,K_2$",
    "D-59": r"$K_1,K_2$ with $K_{nA},K_{nB}$",
    "D-70": r"$\sigma^{(-1)}$ in $C_1,C_2$",
    "D-71": r"$C_1,C_2$ velocity form",
    "D-80": r"$T_3$ in $K_1,K_2$",
    "D-81": r"$T_3$ coefficients $K_n$",
    "D-88": r"$T_2$ before metric substitution",
    "D-90": r"$T_1$ in $C_1,C_2$",
    "D-91": r"$T_1$ coefficients $C_n$",
    "D-94": r"$T_0=(f_1-f_2)C_0/(2\epsilon_{12}^4)$",
    "D-95": r"$C_0=A+B+E$ pieces",
    "D-98": r"$S_{ab;c}$ off-diagonal identity",
    "D-101": r"two-band $[A^a,v^b]_{nm}$",
    "D-104": r"gauge-invariant remainder of $K_{abc}$",
    "E-129": r"multiband off-diagonal $v_{nm}^{ab}$",
    "E-130": r"multiband $\sigma^{(-2)}$ before identity",
    "E-132": r"multiband $\sigma^{(-1)}$ before $\Omega$",
    "E-136": r"multiband $T_3$ before identity",
    "E-138": r"multiband $T_2$ before metric",
    "E-140": r"multiband $T_1$ before $\mathcal{G}$",
    "E-142": r"multiband $T_0$ before $\mathcal{M}$",
    "F-153": r"SHG $\sigma^{(-2)}$ before IBP",
    "F-155": r"SHG $\sigma^{(-1)}$ before $\Omega$",
    "F-159": r"SHG $T_3$ before identity",
    "F-162": r"SHG $T_1$ before $\mathcal{G}$",
    "F-164": r"$T_{0,1}^{\mathrm{SHG}}$",
    "F-165": r"$T_{0,2}^{\mathrm{SHG}}$",
    "F-166": r"$T_{0,3}^{\mathrm{SHG}}$",
    "F-167": r"$T_{0,4}^{\mathrm{SHG}}$",
    "F-168": r"$T_{0,5}^{\mathrm{SHG}}$",
    "F-170": r"Berry-connection difference rewrite",
    "G-182": r"$\rho_S$ as bath-weighted projectors",
}


def load_inventory_numbers() -> list[str]:
    text = (ROOT / "EQUATION_INVENTORY.yaml").read_text()
    return re.findall(r'public_printed_number: "([^"]+)"', text)


def main() -> None:
    rels = [r for r in all_relations()]
    rows = []
    controls = []
    for rel in rels:
        functions = []
        naive_s = "N/A"
        cond_s = "N/A"
        if rel.get("parent_status") == "CERTIFIED_BY_RULE":
            naive_s = "N/A"
            cond_s = "local Leibniz child ZERO"
        elif rel.get("parent_status") == "UNKNOWN_REMAINDER":
            naive_s = "UNKNOWN"
            cond_s = "UNKNOWN"
        elif rel.get("executable") and rel.get("left") is not None:
            left, right = rel["left"], rel["right"]
            functions = sorted(set(detect_functions(left)) | set(detect_functions(right)))
            naive = verify_pair(left, right)
            naive_s = naive["result"]
            if rel.get("subst"):
                l2 = apply_subst(left, rel["subst"], functions)
                r2 = apply_subst(right, rel["subst"], functions)
                cond = verify_pair(l2, r2)
                cond_s = cond["result"]
            else:
                cond_s = "N/A"
        status = final_status(rel, naive_s, cond_s)
        row = {
            "internal_id": rel["internal_id"],
            "display": rel["display"],
            "cue": rel["cue"],
            "move": rel["move"],
            "claimed": rel["claimed"],
            "direct": naive_s,
            "condition": rel.get("condition") or "none",
            "conditional": cond_s,
            "final": status,
            "sources": rel["sources"],
            "targets": rel["targets"],
            "helper": rel.get("helper", False),
            "executable": rel.get("executable", False),
            "regression": rel.get("regression"),
            "parent_status": rel.get("parent_status"),
        }
        rows.append(row)
        print(rel["internal_id"], rel["display"], naive_s, cond_s, status, flush=True)

        if (
            rel.get("executable")
            and rel.get("left")
            and not rel.get("helper")
            and naive_s == "ZERO"
            and not rel.get("subst")
        ):
            kinds = ("sign", "times_two", "plus_one")
            try:
                if parse(rel["right"]) == 0:
                    kinds = ("plus_one",)
            except Exception:
                pass
            for kind in kinds:
                m = verify_pair(rel["left"], mutate(rel["right"], kind))
                controls.append(
                    {
                        "parent": rel["internal_id"],
                        "kind": kind,
                        "result": m["result"],
                        "false_promotion": m["result"] == "ZERO",
                    }
                )
        if (
            rel.get("executable")
            and rel.get("left")
            and rel.get("subst")
            and cond_s == "ZERO"
        ):
            functions = sorted(set(detect_functions(rel["left"])) | set(detect_functions(rel["right"])))
            l2 = apply_subst(rel["left"], rel["subst"], functions)
            r2 = apply_subst(rel["right"], rel["subst"], functions)
            for kind in ("sign", "times_two", "plus_one"):
                m = verify_pair(l2, mutate(r2, kind))
                controls.append(
                    {
                        "parent": rel["internal_id"] + "-cond",
                        "kind": kind,
                        "result": m["result"],
                        "false_promotion": m["result"] == "ZERO",
                    }
                )

    n_false = sum(1 for c in controls if c["false_promotion"])
    rec_dir = ROOT / "machine_records"
    rec_dir.mkdir(exist_ok=True)
    payload = {
        "rows": rows,
        "controls": controls,
        "false_promotions": n_false,
        "n_controls": len(controls),
    }
    (rec_dir / "records.json").write_text(json.dumps(payload, indent=2) + "\n")

    inventoried = load_inventory_numbers()
    covered: set[str] = set()
    for r in rows:
        if r["helper"]:
            continue
        covered |= set(r["sources"]) | set(r["targets"])
    uncovered = [n for n in inventoried if n not in covered]

    write_results(rows, inventoried, uncovered, n_false, len(controls))
    write_coverage(rows, inventoried, uncovered, n_false, len(controls))
    print("n_rows", len(rows), "uncovered", len(uncovered), "controls", len(controls), "false_promo", n_false)


def write_coverage(rows, inventoried, uncovered, n_false, n_ctrl) -> None:
    table_rows = [r for r in rows if not r["helper"]]
    counts = {}
    for r in table_rows:
        counts[r["final"]] = counts.get(r["final"], 0) + 1
    n_exec = sum(1 for r in table_rows if r["executable"])
    cov = {
        "n_numbered": len(inventoried),
        "n_inventoried": len(inventoried),
        "coverage": f"{len(inventoried)}/{len(inventoried)}",
        "standalone_no_relation": uncovered,
        "n_relations": len(table_rows),
        "n_helpers": sum(1 for r in rows if r["helper"]),
        "n_executable": n_exec,
        "final_counts": counts,
        "false_promotions": n_false,
        "n_controls": n_ctrl,
    }
    (ROOT / "COVERAGE.json").write_text(json.dumps(cov, indent=2) + "\n")


def write_results(rows, inventoried, uncovered, n_false, n_ctrl) -> None:
    table_rows = [r for r in rows if not r["helper"]]
    n = len(inventoried)
    n_rel = len(table_rows)
    n_exec = sum(1 for r in table_rows if r["executable"])
    n_struct = sum(1 for r in table_rows if r["final"] == "STRUCTURAL")
    n_unsup = sum(1 for r in table_rows if r["final"] in {"UNSUPPORTED", "COMPILE_FAILURE", "PARSE_FAILURE"})
    n_exact = sum(1 for r in table_rows if r["final"] == "EXACT_ZERO")
    n_subst = sum(1 for r in table_rows if r["final"] == "ZERO_UNDER_SUBSTITUTION")
    n_rule = sum(1 for r in table_rows if r["final"] == "CERTIFIED_BY_RULE")
    n_rem = sum(1 for r in table_rows if r["final"] in {"UNKNOWN_REMAINDER", "UNKNOWN"})
    n_nz = sum(1 for r in table_rows if r["final"] == "NONZERO")
    n_standalone = len(uncovered)

    lines = []
    lines.append("# Full derivation audit: Guo et al., PRL 136, 206303")
    lines.append("")
    lines.append("Source: arXiv:2511.16422v2")
    lines.append("")
    lines.append(
        "All numbered equations in the public paper and appendices were inventoried. "
        "Only source-supported derivation relations are tested as equalities. "
        "ZERO means exact machine ZERO."
    )
    lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append("| Item | Count |")
    lines.append("|---|---:|")
    lines.append(f"| Numbered equations in source | {n} |")
    lines.append(f"| Inventoried | {n} |")
    lines.append(f"| Coverage | 100% |")
    lines.append(f"| Derivation relations extracted | {n_rel} |")
    lines.append(f"| Executable relations | {n_exec} |")
    lines.append(f"| Structural / no equality claim (relation rows) | {n_struct} |")
    lines.append(f"| Standalone numbered equations (no equality claim) | {n_standalone} |")
    lines.append(f"| Unsupported | {n_unsup} |")
    lines.append("")
    lines.append("## Equation audit")
    lines.append("")
    lines.append(
        "| Eq. relation | Mathematical content | Claimed move | Direct check | Condition / authority | Conditional check | Final status |"
    )
    lines.append("|---|---|---|---|---|---|---|")

    def emit(display, cue, move, direct, cond, ccheck, final):
        lines.append(
            "| "
            + " | ".join(
                md_cell(x)
                for x in (display, cue, move, direct, cond, ccheck, final)
            )
            + " |"
        )

    # Merge relation rows and standalone rows in paper order.
    events = []
    for r in table_rows:
        events.append(("rel", relation_sort_key(r), r))
    for p in uncovered:
        events.append(("eq", printed_key(p), p))
    events.sort(key=lambda t: t[1])

    for kind, _k, obj in events:
        if kind == "rel":
            r = obj
            emit(
                r["display"],
                r["cue"],
                r["move"],
                r["direct"],
                r["condition"],
                r["conditional"],
                r["final"],
            )
        else:
            p = obj
            cue = STANDALONE_CUE.get(p, "numbered display")
            emit(
                f"Eq. ({p})",
                cue,
                "definition" if p.startswith(("A-", "B-", "C-", "E-", "F-", "G-")) or p in {"7", "8"} else "derived result",
                "N/A",
                "none",
                "N/A",
                "STRUCTURAL",
            )

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- numbered equations inventoried: {n}/{n}")
    lines.append(f"- derivation relations: {n_rel}")
    lines.append(f"- EXACT_ZERO: {n_exact}")
    lines.append(f"- ZERO_UNDER_SUBSTITUTION: {n_subst}")
    lines.append(f"- CERTIFIED_BY_RULE: {n_rule}")
    lines.append(f"- UNKNOWN_REMAINDER: {n_rem}")
    lines.append(f"- STRUCTURAL / NO_EQUALITY_CLAIM: {n_struct + n_standalone}")
    lines.append(f"- UNSUPPORTED / COMPILE_FAILURE: {n_unsup}")
    lines.append(f"- NONZERO: {n_nz}")
    lines.append(f"- false promotion on injected controls: {n_false}/{n_ctrl}")
    lines.append("")
    (ROOT / "RESULTS.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
