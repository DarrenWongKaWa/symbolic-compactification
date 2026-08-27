"""Re-score frozen P2 JSON with full source texts. Does not call the model."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.grounded_proposer.catalog import catalog_entries
from research.llm_abstraction.secrets import sanitize
from research.llm_abstraction.tasks import load_calibration, load_guo_item
from research.obligation_ir.source_index import build_index
from research.representation_invention.bench.loader import load_dev, load_test
from research.representation_invention.eval.classify import summarize_record
from research.representation_invention.eval.run_experiments import (
    OUT,
    _bench_as_item,
    write_summary,
)
from research.representation_invention.llm.run_p2 import scoring_catalog
from research.representation_invention.llm.score import aggregate_scores, score_hypothesis

RUNS = OUT


def _index(item):
    return build_index(
        item["current"], item.get("symbols") or [], item.get("functions") or [],
    )


def item_for(item_id: str):
    if item_id == "guo-sigma-abc":
        return load_guo_item(), None
    calib = {it["id"]: it for it in load_calibration()}
    if item_id in calib:
        return calib[item_id], None
    bench = {t["id"]: t for t in load_dev() + load_test()}
    if item_id in bench:
        item, cat = _bench_as_item(bench[item_id])
        return item, cat
    return None, None


def rescore_file(path: Path) -> dict:
    rec = json.loads(path.read_text())
    item_id = rec.get("item_id")
    item, cat = item_for(str(item_id))
    if item is None:
        return rec
    entries = cat if cat is not None else catalog_entries(_index(item))
    score_cat = scoring_catalog(item, entries)
    scores = [
        score_hypothesis(
            h,
            score_cat,
            symbols=item.get("symbols") or [],
            functions=item.get("functions") or [],
        )
        for h in rec.get("hypotheses") or []
    ]
    rec["scores"] = scores
    rec.update(aggregate_scores(scores))
    rec["summary"] = summarize_record(rec)
    rec["rescored"] = "full_source_texts"
    path.write_text(json.dumps(sanitize(rec), indent=2, default=str))
    return rec


def main() -> int:
    recs = []
    for path in sorted(RUNS.glob("*.json")):
        rec = rescore_file(path)
        recs.append(rec)
        s = rec.get("summary") or {}
        print(
            path.name,
            rec.get("parse_status"),
            "c", rec.get("compile_status"),
            "Z", rec.get("n_zero"),
            "NZ", rec.get("n_nonzero"),
            "U", rec.get("n_unknown"),
            "dd_ok", s.get("n_dd_ok"),
            "conf", s.get("n_local_confluence"),
        )
    write_summary(recs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
