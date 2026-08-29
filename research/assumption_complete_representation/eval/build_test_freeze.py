"""Write TEST packs, SOL, and freeze manifest. After DEV method selection."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.eval.ac_prompts import (
    build_user_prompt,
    load_condition,
    load_system,
    sha256_text,
)
from research.assumption_complete_representation.eval.test_packs import (
    CHALLENGE,
    CORE,
    DUPLICATE_CONTROL,
    HEADLINE,
    HIDDEN,
    PACKAGING_GAP,
    PUBLIC_PACKS,
)
from research.llm_abstraction.leak import leak_hits
from research.llm_abstraction.packetizer import basic_summary, packets_for_item

HERE = Path(__file__).resolve().parents[1]
PUB = HERE / "packs" / "test" / "public"
HID = HERE / "packs" / "test" / "hidden"
SOL = HERE / "packs" / "test" / "sol"
REND = HERE / "packs" / "test" / "rendered"

PUBLIC_FORBIDDEN = (
    "tweedie", "mehler", "hermite", "divided difference", "ornstein",
    "weyl character", "weyl group", "implicit function theorem", "deq",
    "pontryagin", "matern", "mmse",
)


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def main() -> dict:
    leaks = {}
    hashes = {"public": {}, "hidden": {}, "sol": {}, "rendered": {}}
    for cid, pack in PUBLIC_PACKS.items():
        hits = leak_hits(pack, PUBLIC_FORBIDDEN)
        leaks[cid] = hits
        pp = PUB / f"{cid}.json"
        _dump(pp, pack)
        hashes["public"][cid] = _sha_file(pp)
        hp = HID / f"{cid}.json"
        _dump(hp, HIDDEN[cid])
        hashes["hidden"][cid] = _sha_file(hp)
        basic = basic_summary(pack["current"], pack.get("symbols") or [], pack.get("functions") or [])
        _dump(SOL / f"{cid}.basic.json", basic)
        _pk, _sm, sol_text = packets_for_item(
            {"current": pack["current"], "symbols": pack.get("symbols") or [],
             "functions": pack.get("functions") or [], "hidden_gold": {}},
            cap=10, backends="relations", timeout_s=12.0,
        )
        sp = SOL / f"{cid}.json"
        _dump(sp, {"text": sol_text, "task_id": cid, "backend": "relations", "cap": 10})
        hashes["sol"][cid] = _sha_file(sp)
        for cond in ("P0", "P2"):
            user = build_user_prompt(
                pack, cond, sol_text=sol_text if cond == "P2" else None,
            )
            rp = REND / f"{cid}__{cond}.txt"
            rp.parent.mkdir(parents=True, exist_ok=True)
            rp.write_text(user)
            hashes["rendered"][f"{cid}__{cond}"] = _sha_file(rp)
    freeze = {
        "version": "ac-test-freeze-v1",
        "guo_in_dev_or_test": False,
        "parser_extended": False,
        "prompts_retuned": False,
        "GENERAL_FINAL": "P0",
        "SPECIALIST_DD": "P4",
        "P4_TEST_ELIGIBLE": [],
        "HEADLINE": HEADLINE,
        "DUPLICATE_CONTROL": DUPLICATE_CONTROL,
        "CHALLENGE": CHALLENGE,
        "CORE_COMPARABLE": CORE,
        "PACKAGING_GAP_HEADLINE": PACKAGING_GAP,
        "model": "deepseek-v4-pro",
        "flash_model": "deepseek-v4-flash",
        "seeds": [0, 1, 2, 3, 4],
        "flash_seeds": [0, 1, 2],
        "conditions": ["P0", "P2"],
        "evaluator_version": "ac-eval-v1",
        "compiler_version": "ac-compile-v1.1",
        "scorer_version": "ac-score-v1.3",
        "prompt_hashes": {
            "SYSTEM_V1": sha256_text(load_system()),
            "P0": sha256_text(load_condition("P0")),
            "P2": sha256_text(load_condition("P2")),
        },
        "file_hashes": hashes,
        "leak_scan": leaks,
        "AI_UNIQUE_only_on_CORE_COMPARABLE": True,
        "note": "After this file, no method/prompt/parser/evaluator change.",
    }
    out = HERE / "final"
    out.mkdir(parents=True, exist_ok=True)
    _dump(out / "FREEZE_MANIFEST.json", freeze)
    _dump(HERE / "TEST_MANIFEST.json", {
        "HEADLINE": HEADLINE,
        "CORE_COMPARABLE": CORE,
        "DUPLICATE_CONTROL": DUPLICATE_CONTROL,
        "CHALLENGE": CHALLENGE,
        "GENERAL_FINAL": "P0",
        "guo": False,
        "not_a_prompt_retune": True,
    })
    return {"leaks": leaks, "n_core": len(CORE), "n_headline": len(HEADLINE)}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
