"""Write frozen packs, SOL packets, rendered prompts, and hash manifest."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from research.assumption_complete_representation.eval.ac_prompts import (
    build_user_prompt,
    load_condition,
    load_system,
    sha256_text,
)
from research.assumption_complete_representation.eval.pack_data import (
    CLUSTER_OF,
    CORE,
    HIDDEN,
    P4_ELIGIBLE,
    PACKAGING_GAP,
    PUBLIC_FORBIDDEN,
    PUBLIC_PACKS,
)
from research.llm_abstraction.packetizer import basic_summary, packets_for_item
from research.llm_abstraction.leak import leak_hits

HERE = Path(__file__).resolve().parents[1]
PUB = HERE / "packs" / "dev" / "public"
HID = HERE / "packs" / "dev" / "hidden"
SOL = HERE / "packs" / "dev" / "sol"
REND = HERE / "packs" / "dev" / "rendered"


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def public_blob(pack: dict) -> dict:
    # case_id may contain gold tokens (hermite, dd); never dump it as public.
    return {
        k: pack[k] for k in pack
        if k not in {"hidden", "gold", "latent_structure", "case_id"}
    }


def check_leaks(pack: dict) -> list[str]:
    return leak_hits(public_blob(pack), PUBLIC_FORBIDDEN)


def main() -> dict:
    PUB.mkdir(parents=True, exist_ok=True)
    HID.mkdir(parents=True, exist_ok=True)
    SOL.mkdir(parents=True, exist_ok=True)
    REND.mkdir(parents=True, exist_ok=True)

    leak_report = {}
    hashes = {"packs_public": {}, "packs_hidden": {}, "sol": {}, "basic": {}, "rendered": {}}
    basics = {}
    for cid, pack in PUBLIC_PACKS.items():
        hits = check_leaks(pack)
        leak_report[cid] = hits
        pub_path = PUB / f"{cid}.json"
        _dump(pub_path, public_blob(pack))
        hashes["packs_public"][cid] = _sha_file(pub_path)
        hid_path = HID / f"{cid}.json"
        _dump(hid_path, HIDDEN[cid])
        hashes["packs_hidden"][cid] = _sha_file(hid_path)

        basic = basic_summary(
            pack["current"], pack.get("symbols") or [], pack.get("functions") or [],
        )
        basics[cid] = basic
        basic_path = SOL / f"{cid}.basic.json"
        _dump(basic_path, basic)
        hashes["basic"][cid] = _sha_file(basic_path)

        _pk, _sm, sol_text = packets_for_item(
            {
                "current": pack["current"],
                "symbols": pack.get("symbols") or [],
                "functions": pack.get("functions") or [],
                "hidden_gold": {},
            },
            cap=10,
            backends="relations",
            timeout_s=12.0,
        )
        sol_obj = {"text": sol_text, "task_id": cid, "backend": "relations", "cap": 10}
        sol_path = SOL / f"{cid}.json"
        _dump(sol_path, sol_obj)
        hashes["sol"][cid] = _sha_file(sol_path)

        for cond in ("P0", "P1", "P2", "P3"):
            user = build_user_prompt(
                pack, cond,
                basic_summary=basic if cond == "P1" else None,
                sol_text=sol_text if cond == "P2" else None,
            )
            rp = REND / f"{cid}__{cond}.txt"
            rp.write_text(user)
            hashes["rendered"][f"{cid}__{cond}"] = _sha_file(rp)
        if cid in P4_ELIGIBLE:
            user = build_user_prompt(pack, "P4")
            rp = REND / f"{cid}__P4.txt"
            rp.write_text(user)
            hashes["rendered"][f"{cid}__P4"] = _sha_file(rp)
            # P4 public text must not contain gold type names.
            low = user.lower()
            for tok in ("divided difference", "hermite"):
                if tok in low:
                    leak_report.setdefault(cid, []).append(f"P4_prompt:{tok}")

    prompt_hashes = {
        "SYSTEM_V1": sha256_text(load_system()),
        "P0_RAW": sha256_text(load_condition("P0")),
        "P1_BASIC": sha256_text(load_condition("P1")),
        "P2_SOL": sha256_text(load_condition("P2")),
        "P3_GROUNDED": sha256_text(load_condition("P3")),
        "P4_COALESCENCE": sha256_text(load_condition("P4")),
    }

    freeze = {
        "version": "ac-eval-v1",
        "parent_head": "54d0392",
        "guo_in_dev_or_test": False,
        "parser_extended": False,
        "n_dev": 14,
        "CORE_COMPARABLE": CORE,
        "PACKAGING_GAP": PACKAGING_GAP,
        "cluster_of": CLUSTER_OF,
        "P4_ELIGIBLE": P4_ELIGIBLE,
        "P4_predeclared_before_P0P3": True,
        "p4_seeds": 5,
        "p4_r3_extra_seeds_preauthorized": {
            "sciml-phi-hermite-01": True,
        },
        "p4_extra_used_only_if_ambiguous": True,
        "seeds": [0, 1, 2, 3, 4],
        "model": "deepseek-v4-pro",
        "config_id": "deepseek-v4-pro-thinking-high-v1",
        "reasoning_effort": "high",
        "thinking": {"type": "enabled"},
        "temperature": None,
        "max_tokens": 16384,
        "timeout_s": 180,
        "retries_network": 1,
        "retries_parse": 0,
        "response_format": "json_object",
        "n_hypotheses_max": 5,
        "evaluator_version": "ac-eval-v1",
        "sol_backends": "relations",
        "sol_timeout_s": 12.0,
        "sol_packet_cap": 10,
        "prompt_hashes": prompt_hashes,
        "file_hashes": hashes,
        "leak_scan": leak_report,
        "no_dev_prompt_changes_after_this_file": True,
        "primary_matrix_excludes_packaging_gap": True,
    }
    out = HERE / "DEV_EXECUTION_FREEZE.json"
    _dump(out, freeze)
    return {
        "freeze": str(out),
        "leak_scan": leak_report,
        "n_public": len(PUBLIC_PACKS),
        "n_p4": len(P4_ELIGIBLE),
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
