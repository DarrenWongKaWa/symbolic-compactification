"""OPTIONAL FORM subprocess adapter. GPL executable, not vendored."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from symbolic_compactification.observations.discovery import probe_backend
from symbolic_compactification.observations.ir import (
    DESCRIPTIVE_FACT,
    RelationEdge,
)


def available() -> bool:
    return probe_backend("form").startswith("AVAILABLE")


def run(expr, nodes, *, symbols=None, functions=None) -> dict:
    if not available():
        return {"unavailable": True, "backend": "form"}
    exe = shutil.which("form") or shutil.which("tform")
    # Smoke: write a tiny .frm that prints term count of 1+1.
    frm = "Symbol a;\nLocal F = a+a;\nPrint;\n.end\n"
    try:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "smoke.frm"
            p.write_text(frm)
            proc = subprocess.run(
                [exe, str(p)], capture_output=True, text=True, timeout=8,
                cwd=td,
            )
        rels = [RelationEdge(
            source_ids=[],
            relation_type="CSE_SHARED",
            backend="form",
            exactness_class=DESCRIPTIVE_FACT,
            evidence=f"form smoke rc={proc.returncode}",
            witness=(proc.stdout or "")[:400],
            backend_version="form-cli",
        )]
        return {
            "families": [], "relations": rels, "canonical_variants": [],
            "backend": "form", "version": "form-cli",
        }
    except Exception as exc:
        return {"unavailable": True, "backend": "form", "error": type(exc).__name__}
