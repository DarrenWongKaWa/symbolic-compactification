"""CLI for one Grounded-Proposer-v2 item. Tests mock chat_complete."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.grounded_proposer.catalog import catalog_entries
from research.llm_abstraction.secrets import key_length, key_present, sanitize
from research.llm_abstraction.tasks import load_calibration, load_guo_item
from research.obligation_ir.source_index import build_index
from research.representation_invention.llm.catalog_render import catalog_ids
from research.representation_invention.llm.propose import propose_p2
from research.representation_invention.llm.prompts import SYSTEM_PROMPT, build_p2_user_prompt
from research.representation_invention.llm.score import aggregate_scores, score_hypothesis
from research.structure_discovery.prototype.leakage import proposer_view

OUT_DIR = Path(__file__).resolve().parent / "runs"


def _index(item: dict):
    return build_index(
        item["current"],
        item.get("symbols") or [],
        item.get("functions") or [],
    )


def load_item(item_id: str) -> dict:
    if item_id == "guo-sigma-abc":
        return load_guo_item()
    calib = {it["id"]: it for it in load_calibration()}
    if item_id in calib:
        return calib[item_id]
    raise SystemExit(f"unknown item: {item_id}")


def run_item(
    item: dict,
    *,
    condition: str = "P2",
    seed: int = 0,
    packets_text: Optional[str] = None,
    catalog: Optional[list[dict]] = None,
) -> dict[str, Any]:
    entries = catalog if catalog is not None else catalog_entries(_index(item))
    rec = propose_p2(
        item,
        entries,
        condition=condition,
        packets_text=packets_text,
        seed=seed,
    )
    scores = [
        score_hypothesis(
            h,
            entries,
            symbols=item.get("symbols") or [],
            functions=item.get("functions") or [],
        )
        for h in rec.get("hypotheses") or []
    ]
    rec["scores"] = scores
    rec["seed"] = seed
    rec.update(aggregate_scores(scores))
    return sanitize(rec)


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Grounded-Proposer-v2 (P2/P3/P4)")
    p.add_argument("--item", default="CAL-G-confluence")
    p.add_argument("--condition", default="P2", choices=["P2", "P3", "P4"])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="print prompt metadata only; no API call",
    )
    args = p.parse_args(argv)
    item = load_item(args.item)
    if args.dry_run:
        pub = proposer_view(item)
        entries = catalog_entries(_index(item))
        user = build_p2_user_prompt(
            condition=args.condition,
            expression=pub.get("current") or "",
            catalog_text="(catalog omitted in dry-run summary)",
            packets_text="",
            scientific_context=pub.get("scientific_context") or [],
            symbols=pub.get("symbols") or [],
            functions=pub.get("functions") or [],
        )
        print(
            json.dumps(
                {
                    "item_id": item.get("id"),
                    "condition": args.condition,
                    "seed": args.seed,
                    "n_catalog": len(entries),
                    "system_chars": len(SYSTEM_PROMPT),
                    "user_chars": len(user),
                    "dry_run": True,
                },
                indent=2,
            )
        )
        return 0
    print(f"key_present={int(key_present())} key_len={key_length() if key_present() else 0}")
    if not key_present():
        print("P2 BLOCKED")
        return 2
    rec = run_item(item, condition=args.condition, seed=args.seed)
    out_path = Path(args.out) if args.out else (
        OUT_DIR / f"{item.get('id')}__{args.condition}__s{args.seed}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rec, indent=2, default=str))
    print(
        rec.get("item_id"),
        rec.get("condition"),
        rec.get("parse_status"),
        "hyps", rec.get("n_hypotheses"),
        "ok", rec.get("n_ok"),
        "grounded", rec.get("n_grounded"),
        "compile", rec.get("compile_status"),
        "ZERO", rec.get("n_zero"),
        "NONZERO", rec.get("n_nonzero"),
        "UNKNOWN", rec.get("n_unknown"),
        "wrote", str(out_path),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
