"""Motivating affine polygamma class. Not Guo atoms. No silent genericity."""
from __future__ import annotations

import json
from pathlib import Path

from research.remainder_certification.polygamma import classify_motivating_form
from research.remainder_certification.schema import A_DECLARED, CERTIFIED

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "MOTIVATING_CLASS.json"


def run() -> dict:
    undeclared = classify_motivating_form()
    declared = classify_motivating_form(
        declared_assumptions=[{"class": A_DECLARED, "predicate": "z0 not in Z_<=0"}]
    )
    report = {
        "form": "1/2 + beta*(gamma ± I*(mu-epsilon))/(2*pi) + c*t",
        "undeclared_verdict": undeclared.verdict,
        "undeclared_missing": list(undeclared.missing_assumptions),
        "declared_pole_exclusion_verdict": declared.verdict,
        "certified_without_extra_assumption": undeclared.verdict == CERTIFIED,
        "human_required": undeclared.verdict != CERTIFIED,
        "human_required_predicate": "z0 not in {0,-1,-2,...}",
        "no_guo_atoms": True,
        "no_llm": True,
    }
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
