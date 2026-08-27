"""Freeze v0.2 TEST hashes. Call before run_v02 test."""
from __future__ import annotations

import json
from pathlib import Path

from research.abstraction_invention.beyond.build_v02 import OUT, VERSION, write

ROOT = Path(__file__).resolve().parents[3]


def main():
    write()
    man = json.loads((OUT / "validation" / "freeze_manifest.json").read_text())
    man["frozen"] = True
    man["policy"] = "NO test edits under ssc-abstraction-bench-v0.2-beyond-lgg"
    man["lgg_closed"] = "efc0924"
    (OUT / "validation" / "freeze_manifest.json").write_text(json.dumps(man, indent=2) + "\n")
    dest = ROOT / "research/abstraction_invention/final_v02"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "FREEZE_MANIFEST.json").write_text(json.dumps(man, indent=2) + "\n")
    print("frozen", VERSION, "n", man.get("sha256_by_id") and len(man["sha256_by_id"]))


if __name__ == "__main__":
    main()
