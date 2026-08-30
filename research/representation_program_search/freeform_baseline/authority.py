"""Byte-lock the historical P0 RAW prompt and parser authority."""
from __future__ import annotations

import hashlib
from pathlib import Path

F0_AUTHORITY_COMMIT = "0cdde49"
F0_AUTHORITY_FILES = {
    "research/assumption_complete_representation/prompts/SYSTEM_V1.txt": (
        "6bb2440e1360c3841ac0ef2d193e4dab11aa0460bbe1dbcee0ed0ffecb63094f"
    ),
    "research/assumption_complete_representation/prompts/P0_RAW.txt": (
        "6ccf1fee5020e2db89787302e42cf452ef17206d40358ba1c079c9f52e1c0329"
    ),
    "research/assumption_complete_representation/eval/ac_parser.py": (
        "71bff93ae664d6efa9a4d05854b2aff6c7c24cb6ca68efab6d39f05e96cbfdc6"
    ),
    "research/assumption_complete_representation/eval/ac_prompts.py": (
        "954f12b82317270e478664d8c60872aabb8701eadb1761ea56a6d2ef0bb47dff"
    ),
}


def validate_f0_authority(repository_root: str | Path) -> tuple[str, ...]:
    root = Path(repository_root).resolve()
    failures: list[str] = []
    for relative, expected in sorted(F0_AUTHORITY_FILES.items()):
        path = root / relative
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            failures.append(f"F0_AUTHORITY_MISSING:{relative}")
            continue
        if actual != expected:
            failures.append(f"F0_AUTHORITY_DRIFT:{relative}")
    return tuple(failures)
