"""Re-adjudicate stored LLM hypotheses with the current constructor. No API."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.constructor import construct_and_verify
from research.llm_abstraction.evaluator import evaluate
from research.llm_abstraction.schema import LLMStructureHypothesis, OK, PARSE_FAILURE, ProposeResult
from research.llm_abstraction.tasks import load_calibration, load_dev_primary, load_guo_item

RUNS = Path(__file__).resolve().parent / "runs"


def _hyp(raw: dict) -> LLMStructureHypothesis:
    if (raw.get("parse_status") or OK) == PARSE_FAILURE:
        return LLMStructureHypothesis.parse_failure(raw.get("parse_error") or "parse_failure", raw)
    return LLMStructureHypothesis(
        hypothesis_type=raw["hypothesis_type"],
        target_members=list(raw.get("target_members") or []),
        latent_object=str(raw.get("latent_object") or ""),
        parameters=list(raw.get("parameters") or []),
        operators=list(raw.get("operators") or []),
        instance_maps=list(raw.get("instance_maps") or []),
        construction_plan=str(raw.get("construction_plan") or ""),
        required_assumptions=list(raw.get("required_assumptions") or []),
        proof_obligations=list(raw.get("proof_obligations") or []),
        rationale=str(raw.get("rationale") or ""),
        confidence=float(raw.get("confidence") or 0),
        parse_status=OK,
        quality_flags=list(raw.get("quality_flags") or []),
    )


def _items() -> dict:
    out = {}
    for it in load_calibration() + load_dev_primary():
        out[it["id"]] = it
    g = load_guo_item()
    out[g["id"]] = g
    return out


def rescore() -> dict:
    items = _items()
    n = n_cert_before = n_cert_after = n_unk_before = n_unk_after = 0
    for f in sorted(RUNS.rglob("*.json")):
        if f.name.startswith("frozen") or f.parent.name == "_cache":
            continue
        d = json.loads(f.read_text())
        if "hypotheses" not in d:
            continue
        it = items.get(d.get("item_id"))
        if it is None:
            continue
        n += 1
        old = d.get("eval") or {}
        n_cert_before += int(bool(old.get("certified")))
        n_unk_before += int(old.get("n_unknown") or 0)
        hyps = [_hyp(h) for h in d.get("hypotheses") or []]
        result = ProposeResult(
            hypotheses=hyps,
            parse_status=d.get("parse_status") or OK,
            abstain=bool(d.get("abstain")),
            raw_content=d.get("raw_content") or "",
        )
        cons = [construct_and_verify(h, it.get("symbols") or [], it.get("functions") or [])
                for h in hyps if h.parse_status == OK]
        ev = evaluate(it, result, cons)
        d["constructions"] = cons
        d["eval"] = ev
        d["rescored_constructor"] = "expr_xreplace_v2"
        f.write_text(json.dumps(d, indent=2, default=str))
        n_cert_after += int(bool(ev.get("certified")))
        n_unk_after += int(ev.get("n_unknown") or 0)
    return {
        "n_files": n,
        "certified_before": n_cert_before,
        "certified_after": n_cert_after,
        "unknown_obl_before": n_unk_before,
        "unknown_obl_after": n_unk_after,
    }


if __name__ == "__main__":
    print(json.dumps(rescore(), indent=2))
