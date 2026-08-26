"""Write FREEZE_MANIFEST.json. Call before held-out eval. No method edits after."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from research.structure_discovery.prototype.build_benchmark import OUT, VERSION, write_benchmark

ROOT = Path(__file__).resolve().parents[3]
FINAL = ROOT / "research" / "structure_discovery" / "final"

TRACKED = [
    "research/structure_discovery/prototype/hypothesis.py",
    "research/structure_discovery/prototype/observations.py",
    "research/structure_discovery/prototype/discoverer.py",
    "research/structure_discovery/prototype/constructor.py",
    "research/structure_discovery/prototype/orchestrator.py",
    "research/structure_discovery/prototype/evaluator.py",
    "research/structure_discovery/prototype/baselines.py",
    "roles/SCIENTIFIC_STRUCTURE_DISCOVERER.md",
    "roles/STRUCTURE_CONSTRUCTOR.md",
    "research/structure_discovery/protocol/CLAIMS.md",
    "research/structure_discovery/ABSTRACTION_TAXONOMY.md",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_sha() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                       capture_output=True, text=True)
    return r.stdout.strip() or "unknown"


def main() -> None:
    write_benchmark()
    items = {}
    for p in sorted((OUT / "dev").glob("*.json")) + sorted((OUT / "test").glob("*.json")):
        items[p.stem] = sha(p)
    manifest = {
        "version": "structure-discovery-v1",
        "benchmark": VERSION,
        "engine": "0.3.0",
        "method": "B9_observe_hypothesis_construct_verify_deterministic",
        "llm": None,
        "llm_blocked": "ANTHROPIC_AUTH_TOKEN length 35; no OpenAI/Gemini/xAI",
        "seeds": ["deterministic"],
        "verify_budget_s": 8,
        "max_hypotheses": 8,
        "git_sha_at_freeze": git_sha(),
        "file_sha256": {p: sha(ROOT / p) for p in TRACKED},
        "benchmark_sha256_by_id": items,
        "n_dev": sum(1 for _ in (OUT / "dev").glob("*.json")),
        "n_test": sum(1 for _ in (OUT / "test").glob("*.json")),
        "guo_in_test": False,
        "frozen": True,
        "policy": "NO method/prompt/metric/test-set edits under this version",
    }
    FINAL.mkdir(parents=True, exist_ok=True)
    (OUT / "validation" / "freeze_manifest.json").write_text(
        json.dumps({**manifest, "scope": "benchmark"}, indent=2) + "\n"
    )
    (FINAL / "FREEZE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"frozen": True, "n_test": manifest["n_test"],
                      "n_dev": manifest["n_dev"]}, indent=2))


if __name__ == "__main__":
    main()
