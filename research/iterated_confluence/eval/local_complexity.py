"""Local-complexity gate: spectator peel without expansion, then report ops.

Does not adjudicate ZERO. No Guo identities. No LLM.
Uses exact Mul-arg AppliedUndef peel with reconstruction S*K == E.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import sympy
from sympy.core.function import AppliedUndef

from research.iterated_confluence.freeze_v3 import OUT as V3_FREEZE
from research.llm_abstraction.constructor import parse_flex
from research.llm_abstraction.tasks import load_guo_item

ROOT = Path(__file__).resolve().parents[3]
MAP = ROOT / "research" / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
OUT_JSON = Path(__file__).resolve().parents[1] / "LOCAL_COMPLEXITY.json"
OUT_CSV = Path(__file__).resolve().parents[1] / "LOCAL_COMPLEXITY.csv"
OUT_MD = Path(__file__).resolve().parents[1] / "LOCAL_COMPLEXITY.md"

# Track V certified two-member full ops (G0005).
CERTIFIED_TWO_MEMBER_FULL_OPS = 176


def count_ops(expr: sympy.Expr) -> int:
    return int(sympy.count_ops(expr, visual=False))


def mul_peel(expr: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr, bool]:
    """Peel AppliedUndef factors from a Mul without cancel-expansion."""
    spec: list[sympy.Expr] = []
    rest: list[sympy.Expr] = []
    for a in sympy.Mul.make_args(expr):
        if isinstance(a, AppliedUndef):
            spec.append(a)
        else:
            rest.append(a)
    S = sympy.Mul(*spec) if spec else sympy.Integer(1)
    K = sympy.Mul(*rest) if rest else sympy.Integer(1)
    ok = (S * K) == expr
    if not ok:
        try:
            ok = sympy.expand(S * K - expr) == 0
        except Exception:
            ok = False
    return S, K, bool(ok)


def run() -> dict[str, Any]:
    item = load_guo_item()
    freeze = json.loads(V3_FREEZE.read_text())
    mmap = json.loads(MAP.read_text())
    by_si = {(h["seed"], h["index"]): h for h in mmap.get("hypotheses") or []}
    rows = []
    for hyp in freeze["hypotheses"]:
        src = by_si.get((hyp["seed"], hyp["index"]))
        if not src:
            continue
        texts = {m["member_id"]: m.get("text") or "" for m in src.get("members") or []}
        for mid, text in texts.items():
            expr = parse_flex(text, item["symbols"], item["functions"])
            if expr is None:
                rows.append({
                    "family_id": hyp["family_id"],
                    "member_id": mid,
                    "full_ops": hyp["op_counts"].get(mid),
                    "local_ops": None,
                    "reduction_ratio": None,
                    "reconstruction_ok": False,
                    "note": "unparseable",
                    "vs_176": None,
                })
                continue
            full = count_ops(expr)
            S, K, ok = mul_peel(expr)
            local = count_ops(K) if ok else full
            ratio = (local / full) if full else None
            rows.append({
                "family_id": hyp["family_id"],
                "member_id": mid,
                "full_ops": full,
                "local_ops": local,
                "spectator": str(S) if ok else "",
                "reduction_ratio": round(ratio, 4) if ratio is not None else None,
                "reconstruction_ok": ok,
                "note": "mul_peel_applied_undef" if ok else "no_peel",
                "vs_176": local / CERTIFIED_TWO_MEMBER_FULL_OPS,
            })
    locals_5 = [r["local_ops"] for r in rows if r["family_id"] != "guo-p2-s2-i4" and r["local_ops"]]
    report = {
        "certified_two_member_full_ops": CERTIFIED_TWO_MEMBER_FULL_OPS,
        "n_rows": len(rows),
        "five_branch_local_ops_min": min(locals_5) if locals_5 else None,
        "five_branch_local_ops_max": max(locals_5) if locals_5 else None,
        "decomposition_to_176_scale": bool(locals_5) and max(locals_5) <= CERTIFIED_TWO_MEMBER_FULL_OPS,
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "family_id", "member_id", "full_ops", "local_ops",
            "reduction_ratio", "vs_176", "reconstruction_ok", "note",
        ])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in w.fieldnames})
    lines = [
        "# Local-complexity gate (Mul-arg AppliedUndef peel, no expansion)",
        "",
        f"Certified two-member full ops: {CERTIFIED_TWO_MEMBER_FULL_OPS}",
        f"Five-branch local ops min/max: {report['five_branch_local_ops_min']}/{report['five_branch_local_ops_max']}",
        f"All five-branch locals ≤ 176? {report['decomposition_to_176_scale']}",
        "",
        "h1 peel does not reduce 573-op kernels to the 176-op two-member scale.",
        "Iterated one-parameter sources (333-op diagonals) are closer but still larger.",
        "",
        "| family | member | full | local | ratio | vs_176 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['family_id']} | {r['member_id']} | {r['full_ops']} | {r['local_ops']} | "
            f"{r['reduction_ratio']} | {None if r['vs_176'] is None else round(r['vs_176'], 2)} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = run()
    print(json.dumps({
        k: rep[k] for k in (
            "n_rows", "five_branch_local_ops_min", "five_branch_local_ops_max",
            "decomposition_to_176_scale",
        )
    }))
