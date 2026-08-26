"""DEV case studies. Guo is never held-out evidence."""
from __future__ import annotations

import json
from pathlib import Path

from research.structure_discovery.prototype.baselines import run_b9
from research.structure_discovery.prototype.build_benchmark import OUT, write_benchmark
from research.structure_discovery.prototype.evaluator import score_run
from research.structure_discovery.prototype.leakage import proposer_view
from research.structure_discovery.prototype.observations import (
    observe_expression,
    observe_parsed,
)
from research.structure_discovery.prototype.discoverer import hypotheses_from_observations
from symbolic_compactification.adapters import (
    extract_expression_text,
    translate_wolfram_text,
)
from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import parse_expression

ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / "research" / "structure_discovery" / "case_studies"

PHYSICS_DEV_IDS = [
    "S2-pos-kubo-double",
    "S2-pos-green-resolvent",
    "S2-pos-thermal-pair",
    "S3-pos-transport-kernel",
    "S3-pos-scattering-kernel",
    "S3-pos-matsubara-pair",
]


def _item(iid: str) -> dict:
    return json.loads((OUT / "dev" / f"{iid}.json").read_text())


def run_physics_cases() -> list[dict]:
    write_benchmark()
    out = []
    for iid in PHYSICS_DEV_IDS:
        item = _item(iid)
        run = run_b9(item)
        sc = score_run(item, run)
        out.append({
            "id": iid,
            "family": item.get("family"),
            "gold_types": item.get("gold_types"),
            "type_hit": sc["axis_A_type_hit"],
            "gold_certified": sc["axis_C_gold_type_certified"],
            "unsafe_merge": sc["axis_C_unsafe_merge"],
            "types": run.get("hypothesis_types"),
            "d_certified": run.get("d_certified"),
            "n_zero": run.get("n_zero"),
            "n_nonzero": run.get("n_nonzero"),
            "n_unknown": run.get("n_unknown"),
            "structured": run.get("certified_structured"),
            "human_interpretation_slot": {
                "what_structure_became_visible": None,
                "why_useful": None,
                "further_derivation": None,
                "physical_interpretation": None,
                "status": "HUMAN_REQUIRED",
            },
        })
    return out


def run_guo_diagnostic() -> dict:
    """Observe + hypothesize only. No gold names in the payload."""
    raw = (ROOT / "examples" / "long" / "Guo_Sigma_abc_dc_exact.txt").read_text()
    rec = {
        "id": "S3-dev-guo-sigma-abc",
        "split": "dev",
        "note": "DEV/CASE STUDY only. Not held-out evidence.",
        "gold_names_shown": False,
    }
    try:
        tr = translate_wolfram_text(extract_expression_text(raw))
        rec["translated_chars"] = len(tr.text)
        rec["translation_ok"] = True
        rec["n_symbols"] = len(tr.symbols)
        rec["n_functions"] = len(tr.functions)
        rec["count_ops"] = int(__import__("sympy").count_ops(tr.expr))
    except Exception as exc:
        rec["translation_ok"] = False
        rec["error"] = f"{type(exc).__name__}:{exc}"
        return rec
    try:
        obs = observe_parsed(tr.expr)
        rec["observation_ok"] = True
        rec["n_repeated"] = len(obs.get("repeated_subtrees") or [])
        rec["n_perm"] = len(obs.get("permutation_pairs") or [])
        rec["n_piecewise"] = len(obs.get("piecewise") or [])
        rec["n_denoms"] = len(obs.get("denominators") or [])
        rec["structure_summary"] = obs.get("structure_summary")
        hyps = hypotheses_from_observations(obs, max_hypotheses=8)
        rec["hypothesis_types"] = [h.hypothesis_type for h in hyps]
        rec["d_attempted"] = sorted({h.d_level for h in hyps})
        rec["claimed_structures"] = [h.claimed_structure for h in hyps]
        rec["concrete_not_generic_phrase"] = all(
            bool(h.target_subexpressions) and bool(h.construction_plan)
            for h in hyps
        )
        rec["independent_l4_l7"] = False
        rec["note_l2"] = (
            "Types may include kernels/orbits; this is not PRB L4–L7 discovery."
        )
    except AdapterError as exc:
        rec["observation_ok"] = False
        rec["error"] = exc.code
    except Exception as exc:
        rec["observation_ok"] = False
        rec["error"] = f"{type(exc).__name__}:{exc}"
    rec["human_interpretation_slot"] = {
        "status": "HUMAN_REQUIRED",
        "note": "Do not invent PRB L4–L7 meaning. Previous line stopped at L2.",
    }
    return rec


def main() -> None:
    CASE.mkdir(parents=True, exist_ok=True)
    physics = run_physics_cases()
    guo = run_guo_diagnostic()
    (CASE / "PHYSICS_CASES.json").write_text(json.dumps(physics, indent=2) + "\n")
    (CASE / "GUO_DIAGNOSTIC.json").write_text(json.dumps(guo, indent=2) + "\n")
    lines = ["# Structure-discovery case studies", "",
             "Guo is DEV only. Human interpretation slots are unfilled.", ""]
    for p in physics:
        lines.append(
            f"- `{p['id']}` family={p['family']} type_hit={p['type_hit']} "
            f"goldZ={p['gold_certified']} types={p['types']}"
        )
    lines += ["", "## Guo", "",
              f"translation_ok={guo.get('translation_ok')} "
              f"observation_ok={guo.get('observation_ok')} "
              f"types={guo.get('hypothesis_types')} error={guo.get('error')}",
              "",
              "Previous compactification line: certified form stayed at L2. "
              "This case study does not claim L4–L7.", ""]
    (CASE / "README.md").write_text("\n".join(lines))
    print(json.dumps({"n_physics": len(physics), "guo": {
        k: guo.get(k) for k in (
            "translation_ok", "observation_ok", "hypothesis_types", "error",
            "prefix_parse",
        )
    }}, indent=2))


if __name__ == "__main__":
    main()
