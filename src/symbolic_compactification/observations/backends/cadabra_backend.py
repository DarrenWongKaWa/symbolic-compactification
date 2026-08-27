"""OPTIONAL Cadabra2 subprocess adapter. GPL stays out of process."""
from __future__ import annotations

import shutil
import subprocess

from symbolic_compactification.observations.discovery import probe_backend
from symbolic_compactification.observations.ir import (
    DESCRIPTIVE_FACT,
    RelationEdge,
)


def available() -> bool:
    return probe_backend("cadabra").startswith("AVAILABLE")


def run(expr, nodes, *, symbols=None, functions=None) -> dict:
    if not available():
        return {"unavailable": True, "backend": "cadabra"}
    exe = shutil.which("cadabra2") or shutil.which("cadabra")
    try:
        proc = subprocess.run(
            [exe, "--version"],
            capture_output=True, text=True, timeout=5,
        )
        ver = (proc.stdout or proc.stderr or "").strip()[:200]
    except Exception as exc:
        return {"unavailable": True, "backend": "cadabra",
                "error": type(exc).__name__}
    # Narrow interchange is documented; no tensor properties were declared
    # for this call, so we only record availability metadata.
    rels = [RelationEdge(
        source_ids=[],
        relation_type="TENSOR_SYMMETRY_RELATED",
        backend="cadabra",
        exactness_class=DESCRIPTIVE_FACT,
        evidence="cadabra present; no index declarations in this observe() call",
        backend_version=ver or "cadabra2",
        assumptions=["requires explicit index/tensor property input"],
    )]
    return {
        "families": [], "relations": rels, "canonical_variants": [],
        "backend": "cadabra", "version": ver,
    }
