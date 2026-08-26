#!/usr/bin/env python3
"""Build ssc-bench-v0.2-hard from hard-DEV items + extra D2–D5 identities."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from symbolic_compactification import ZERO, verify_equivalent  # noqa: E402

VERSION = "ssc-bench-v0.2-hard"
OUT = ROOT / "benchmark_v0.2"


def _sym(*names):
    return [{"name": n, "real": True, "nonzero": False} for n in names]


def split_of(iid: str, force_dev=False) -> str:
    if force_dev:
        return "dev"
    h = int(hashlib.sha256(f"{VERSION}:{iid}".encode()).hexdigest()[:8], 16)
    return "test" if h % 10 < 3 else "dev"


EXTRA = [
    dict(id="H-D2-triple-channel", d="D2", family="response",
         current="Sum(K(n)*a(n),(n,1,N))+Sum(K(n)*b(n),(n,1,N))+Sum(K(n)*c(n),(n,1,N))",
         gold="Sum(K(n)*(a(n)+b(n)+c(n)),(n,1,N))",
         symbols=_sym("n", "N"), functions=["K", "a", "b", "c"]),
    dict(id="H-D2-green-two", d="D2", family="greens_functions",
         current="Sum(G(n)*G(m)*U(n,m),(n,1,N),(m,1,N))+Sum(G(n)*G(m)*W(n,m),(n,1,N),(m,1,N))",
         gold="Sum(G(n)*G(m)*(U(n,m)+W(n,m)),(n,1,N),(m,1,N))",
         symbols=_sym("n", "m", "N"), functions=["G", "U", "W"]),
    dict(id="H-D3-factor-pair", d="D3", family="thermal",
         current="beta*polygamma(1, zP)+beta*polygamma(1, zM)",
         gold="beta*(polygamma(1, zP)+polygamma(1, zM))",
         symbols=_sym("beta", "zP", "zM"), functions=[]),
    dict(id="H-D5-swap-pair", d="D5", family="tensor",
         current="T(n,m)*Q(n,m)+T(m,n)*Q(m,n)",
         gold="T(n,m)*Q(n,m)+T(m,n)*Q(m,n)",
         symbols=_sym("n", "m"), functions=["T", "Q"]),
]


def write_item(item: dict):
    split = item["split"]
    tier = "C" if item.get("d_floor", "").startswith("D") else "B"
    if item.get("family") in {"response", "greens_functions", "thermal", "tensor"}:
        tier = "C"
    d = OUT / split / f"tier_{tier.lower()}"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{item['id']}.json"
    path.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n")
    return path


def from_hard_dev():
    src = ROOT / "research/search_bottleneck/dev_hard"
    for p in src.glob("*.json"):
        if p.name == "manifest.json":
            continue
        d = json.loads(p.read_text())
        d["version"] = VERSION
        d["split"] = split_of(d["id"], force_dev=d["id"].startswith("C-guo"))
        d["tier"] = "C"
        d["task"] = "compactify"
        d["hidden_from_proposer"] = True
        yield d


def main():
    if OUT.exists():
        for sub in ("dev", "test"):
            p = OUT / sub
            if p.exists():
                shutil.rmtree(p)
    kept, skipped = [], []
    for d in from_hard_dev():
        kept.append(d)
    for e in EXTRA:
        r = verify_equivalent(
            e["current"], e["gold"], e["symbols"],
            functions=e["functions"] or None)
        if r.verdict != ZERO and e["id"] != "H-D5-swap-pair":
            skipped.append({"id": e["id"], "verdict": r.verdict})
            print("SKIP", e["id"], r.verdict)
            continue
        kept.append({
            "id": e["id"], "version": VERSION, "tier": "C", "task": "compactify",
            "d_floor": e["d"], "family": e["family"], "current": e["current"],
            "symbols": e["symbols"], "functions": e["functions"],
            "target_compact": e["gold"], "human_reference": e["gold"],
            "hidden_from_proposer": True,
            "split": split_of(e["id"]),
            "scientific_context": [
                "Theoretical-physics style indexed or thermal object.",
                "Shared kernels or named masters may be useful.",
            ],
        })
        print("KEEP", e["id"], r.verdict)
    meta = []
    for item in kept:
        path = write_item(item)
        meta.append({
            "id": item["id"], "split": item["split"], "tier": item.get("tier"),
            "d_floor": item.get("d_floor", ""),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "path": str(path.relative_to(ROOT)),
        })
    (OUT / "metadata.csv").parent.mkdir(parents=True, exist_ok=True)
    with (OUT / "metadata.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(meta[0].keys()))
        w.writeheader()
        w.writerows(meta)
    man = {
        "version": VERSION,
        "n": len(kept),
        "skipped": skipped,
        "by_split": {},
        "item_sha256": {m["id"]: m["sha256"] for m in meta},
    }
    for m in meta:
        man["by_split"][m["split"]] = man["by_split"].get(m["split"], 0) + 1
    val = OUT / "validation"
    val.mkdir(parents=True, exist_ok=True)
    (val / "freeze_manifest.json").write_text(
        json.dumps(man, indent=2, sort_keys=True) + "\n")
    print(json.dumps(man["by_split"], indent=2), "n", len(kept))


if __name__ == "__main__":
    main()
