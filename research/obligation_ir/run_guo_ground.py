"""Ground frozen Guo hypotheses to source. No LLM. No SOL edits."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.packetizer import observe_cached
from research.llm_abstraction.tasks import load_guo_item
from research.obligation_ir.grounding import (
    AMBIGUOUS_BIND,
    EXACT_BIND,
    NO_BIND,
    UNIQUE_STRUCTURAL_BIND,
    bind_hypothesis_members,
)
from research.obligation_ir.guo import G1_TYPES, g1_discovery
from research.obligation_ir.repr_compile import (
    compile_confluence,
    compile_dd,
    compile_derivative_identities,
)
from research.llm_abstraction.schema import LLMStructureHypothesis, OK
from research.obligation_ir.source_index import build_index

FROZEN = ROOT / "research" / "llm_abstraction" / "runs" / "guo"
OUT = ROOT / "research" / "obligation_ir"
CSV_PATH = OUT / "GUO_GROUNDING.csv"
MD_PATH = OUT / "GUO_GROUNDING.md"


def _hyp(raw: dict) -> dict:
    return raw


def main() -> None:
    item = load_guo_item()
    sol = observe_cached(
        item["current"], item["symbols"], item.get("functions") or [],
        backends="relations", timeout_s=180.0,
    )
    index = build_index(
        item["current"], item["symbols"], item.get("functions") or [],
        sol_nodes=sol.get("nodes") or [],
    )
    print("source_nodes", len(index.nodes),
          "sums", sum(1 for n in index.nodes if n.kind == "sum"),
          "branches", sum(1 for n in index.nodes if n.kind == "piecewise_branch"))
    rows = []
    n_hyp = 0
    for f in sorted(FROZEN.glob("*.json")):
        d = json.loads(f.read_text())
        hyps = d.get("hypotheses") or []
        g1 = g1_discovery([
            LLMStructureHypothesis(
                hypothesis_type=h["hypothesis_type"],
                target_members=h.get("target_members") or [],
                latent_object=h.get("latent_object") or "",
                parameters=h.get("parameters") or [],
                operators=h.get("operators") or [],
                instance_maps=h.get("instance_maps") or [],
                construction_plan=h.get("construction_plan") or "",
                required_assumptions=h.get("required_assumptions") or [],
                proof_obligations=h.get("proof_obligations") or [],
                rationale=h.get("rationale") or "",
                confidence=float(h.get("confidence") or 0),
            ) for h in hyps if h.get("hypothesis_type")
        ])
        for hi, h in enumerate(hyps):
            n_hyp += 1
            htype = h.get("hypothesis_type") or ""
            binds = bind_hypothesis_members(
                h, index,
                symbols=item["symbols"],
                functions=item.get("functions") or [],
            )
            conf = Counter(b.confidence for b in binds)
            admissible = [b for b in binds if b.admissible]
            dd_rows = compile_dd(
                h, binds, index,
                symbols=item["symbols"], functions=item.get("functions") or [],
            ) if htype == "divided_difference" else []
            cf_rows = compile_confluence(
                h, binds, index,
                symbols=item["symbols"], functions=item.get("functions") or [],
            ) if htype in {"confluent_representation", "divided_difference"} else []
            dv_rows = compile_derivative_identities(
                h, binds,
                symbols=item["symbols"], functions=item.get("functions") or [],
            ) if htype in {"derivative_family", "master_function"} else []
            verdicts = [v.verdict for _, v in dd_rows + cf_rows + dv_rows]
            if not binds:
                interp = "no_members"
            elif not admissible and conf[AMBIGUOUS_BIND]:
                interp = "ambiguous_bind"
            elif not admissible:
                interp = "no_bind"
            elif "ZERO" in verdicts and "NONZERO" not in verdicts and "UNKNOWN" not in verdicts:
                interp = "old_discovery_real"
            elif "NONZERO" in verdicts and "ZERO" not in verdicts:
                interp = "wrong_abstraction"
            elif "UNKNOWN" in verdicts and "ZERO" not in verdicts and "NONZERO" not in verdicts:
                interp = "verifier_bottleneck"
            elif "ZERO" in verdicts:
                interp = "mixed_zero_and_rest"
            elif dd_rows or cf_rows:
                interp = "compiled_no_zero"
            else:
                interp = "bound_not_compiled"
            rows.append({
                "file": f.name,
                "condition": d.get("condition"),
                "seed": d.get("seed"),
                "hyp_i": hi,
                "type": htype,
                "g1_run": g1["pass"],
                "n_aliases": len(binds),
                "n_exact": conf[EXACT_BIND],
                "n_unique": conf[UNIQUE_STRUCTURAL_BIND],
                "n_ambiguous": conf[AMBIGUOUS_BIND],
                "n_nobind": conf[NO_BIND],
                "n_dd": len(dd_rows),
                "n_conf": len(cf_rows),
                "n_deriv": len(dv_rows),
                "verdicts": "|".join(verdicts) if verdicts else "",
                "interpretation": interp,
                "bind_evidence": "; ".join(
                    f"{b.alias[:40]}:{b.confidence}:{b.evidence}:{b.gid}" for b in binds[:6]
                ),
            })
    fields = list(rows[0].keys()) if rows else []
    with CSV_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    # markdown table of G1 types DD/confluence/derivative
    focus = [r for r in rows if r["type"] in {
        "divided_difference", "confluent_representation", "derivative_family", "master_function",
    }]
    lines = [
        "# Frozen Guo source grounding (Track B)",
        "",
        "No new LLM calls. Frozen `runs/guo` hypotheses only.",
        "Admissible binds: EXACT_BIND and UNIQUE_STRUCTURAL_BIND.",
        "AMBIGUOUS_BIND and NO_BIND are not sent to the verifier.",
        "",
        f"Source inventory: {len(index.nodes)} nodes "
        f"({sum(1 for n in index.nodes if n.kind=='sum')} sums, "
        f"{sum(1 for n in index.nodes if n.kind=='piecewise_branch')} branches).",
        "",
        "| cond | type | exact | unique | amb | nobind | DD | conf | deriv | verdicts | interpretation |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in focus:
        lines.append(
            f"| {r['condition']}s{r['seed']} | {r['type']} | {r['n_exact']} | {r['n_unique']} | "
            f"{r['n_ambiguous']} | {r['n_nobind']} | {r['n_dd']} | {r['n_conf']} | {r['n_deriv']} | "
            f"{r['verdicts'] or '—'} | {r['interpretation']} |"
        )
    c = Counter(r["interpretation"] for r in focus)
    lines += [
        "",
        "## Interpretation counts (DD / confluence / derivative / master only)",
        "",
    ]
    for k, v in c.most_common():
        lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        "## What this is allowed to claim",
        "",
        "If a row is `old_discovery_real`, that is **compiler/grounding gain** on a",
        "frozen discovery, not a new DeepSeek success.",
        "If `wrong_abstraction`, the frozen text used DD/confluence words but the",
        "bound source branch is not the Newton form (D, previously masked by C).",
        "If `verifier_bottleneck`, binding and compilation succeeded (V).",
        "If `no_bind` / `ambiguous_bind`, still C (cannot ground aliases).",
        "",
        "T1 A2 = 4/5 D remains a frozen negative: SOL induces an abstraction prior.",
        "Do not retune SOL to erase it.",
        "",
    ]
    MD_PATH.write_text("\n".join(lines) + "\n")
    print("wrote", CSV_PATH, "n", len(rows), "focus", len(focus))
    print("interp", c)
    print("conf", Counter((r["n_exact"], r["n_unique"], r["n_ambiguous"], r["n_nobind"]) for r in focus))


if __name__ == "__main__":
    main()
