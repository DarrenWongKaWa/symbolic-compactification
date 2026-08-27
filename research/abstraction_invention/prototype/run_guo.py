"""Guo DEV case study: invent families, do not compactify σ_abc."""
from __future__ import annotations

import json
from pathlib import Path

from research.abstraction_invention.prototype.inventor import invent_from_parsed
from symbolic_compactification.adapters import extract_expression_text, translate_wolfram_text

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "research" / "abstraction_invention" / "case_studies"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = (ROOT / "examples" / "long" / "Guo_Sigma_abc_dc_exact.txt").read_text()
    rec = {
        "id": "guo-sigma-abc",
        "split": "dev",
        "task": (
            "Identify families of mathematically related subexpressions that "
            "are not exact syntactic duplicates. Propose the smallest "
            "parameterized object that could generate all members. Do not "
            "propose a final compact expression."
        ),
        "gold_names_shown": False,
    }
    try:
        tr = translate_wolfram_text(extract_expression_text(raw))
        rec["translation_ok"] = True
        rec["count_ops"] = int(__import__("sympy").count_ops(tr.expr))
    except Exception as exc:
        rec["translation_ok"] = False
        rec["error"] = f"{type(exc).__name__}:{exc}"
        (OUT / "GUO.json").write_text(json.dumps(rec, indent=2) + "\n")
        print(json.dumps(rec, indent=2))
        return
    hyps = invent_from_parsed(tr.expr)
    rec["n_hypotheses"] = len(hyps)
    rec["operators"] = [h.operator for h in hyps]
    rec["templates"] = [
        {"operator": h.operator, "template": h.template,
         "family": h.family[:4], "n_members": len(h.family),
         "reason": h.reason}
        for h in hyps
    ]
    rec["has_antiunification"] = "antiunification" in rec["operators"]
    rec["has_confluence"] = "confluence" in rec["operators"]
    rec["has_master_derivative"] = "master_derivative" in rec["operators"]
    rec["independent_l4_l7"] = False
    rec["human_slot"] = "HUMAN_REQUIRED"
    (OUT / "GUO.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({k: rec[k] for k in rec if k != "templates"}, indent=2))
    print("templates", json.dumps(rec["templates"][:8], indent=2)[:2000])


if __name__ == "__main__":
    main()
