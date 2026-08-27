"""Frozen-artifact integrity for the representation-invention line.

Compares working-tree bytes of historical experiment files to 3fea222.
Does not rewrite those files.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
PARENT = "3fea222"
FROZEN_GLOBS = (
    "research/llm_abstraction/runs/**/*.json",
    "research/grounded_proposer/runs/**/*.json",
    "research/obligation_ir/results/**/*.json",
    "research/obligation_ir/RESULTS_FROZEN.csv",
    "research/obligation_ir/GUO_GROUNDING.csv",
    "src/symbolic_compactification/observations/**/*.py",
)


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def frozen_paths() -> list[Path]:
    out: list[Path] = []
    for g in FROZEN_GLOBS:
        out.extend(ROOT.glob(g))
    return [p for p in out if p.is_file()]


def diff_against_parent(paths: Iterable[Path] | None = None) -> list[str]:
    """Return relative paths that differ from PARENT."""
    rels = []
    for p in paths if paths is not None else frozen_paths():
        rel = str(p.relative_to(ROOT))
        try:
            _git("cat-file", "-e", f"{PARENT}:{rel}")
        except subprocess.CalledProcessError:
            # file did not exist at parent — not a frozen mutation
            continue
        cur = _git("hash-object", rel).strip()
        old = _git("rev-parse", f"{PARENT}:{rel}").strip()
        if cur != old:
            rels.append(rel)
    return rels


def assert_frozen_intact() -> None:
    dirty = diff_against_parent()
    if dirty:
        raise AssertionError("frozen artifacts mutated:\n" + "\n".join(dirty))
