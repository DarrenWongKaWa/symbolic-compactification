"""v0.2.2 audit-delta: deterministic structural ordering (anti-regression).

``Expr.atoms()`` returns a SET: its iteration order depends on
``PYTHONHASHSEED`` and is therefore irreproducible across processes. The
engine's construction/pairing/hashing/comparison paths must go through
``ordered_atoms`` / ``canonical_structure_items`` instead.

Regression coverage on a Sum/Piecewise-heavy synthetic expression:

* (a) STABLE in-process: repeated calls return the identical ordered lists.
* (b) IDENTICAL ordered output and content hash across >=3 FRESH
      subprocess runs with DIFFERENT ``PYTHONHASHSEED`` values — the direct
      anti-regression for unordered-set iteration.
* (c) the helpers feed the structure summaries: ``structure_summary`` counts
      equal the canonical item counts, and the full structural payload hash
      of the same expression is equal across processes.

Neutral synthetic fixtures only; each subprocess is a small ``python -c``
run (sympy import dominates; the whole file stays well under ~15s).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import sympy

from symbolic_compactification import (
    canonical_json,
    canonical_structure_items,
    ordered_atoms,
    sha256_text,
    structure_summary,
)

# The engine source root, so subprocesses import THIS checkout regardless of
# what is installed site-wide.
_SRC = str(Path(__file__).resolve().parents[1] / "src")

# Distinct hash seeds: the anti-regression demands DIFFERENT seeds across
# fresh processes (a seed-dependent ordering would diverge here).
_HASH_SEEDS = ("0", "1", "20260820")


def _build_heavy_expression() -> sympy.Expr:
    """Sum/Piecewise-heavy synthetic expression (multiple sums, products,
    multi-branch piecewises, indexed function calls, several free symbols)."""
    n, k = sympy.symbols("n k", real=True)
    N, M = sympy.symbols("N M", real=True)
    x = sympy.Symbol("x", real=True)
    f, g, h = (sympy.Function("f"), sympy.Function("g"), sympy.Function("h"))
    return (
        sympy.Sum(f(n) * g(n), (n, 1, N))
        + sympy.Sum(h(k), (k, 0, M))
        + sympy.Sum(n**2, (n, 1, N))
        + sympy.Piecewise((x, x > 0), (-x, x < 0), (0, True))
        + sympy.Piecewise((f(n), n >= 1), (0, True))
        + sympy.Product(f(n), (n, 1, N))
    )


def _ordered_payload(expr: sympy.Expr) -> dict:
    """The full ordered structural payload under test: atom order, canonical
    structure items and the structure summary that consumes them."""
    return {
        "atoms": [sympy.srepr(a) for a in ordered_atoms(expr)],
        "sums_atoms": [sympy.srepr(a) for a in ordered_atoms(expr, sympy.Sum)],
        "items": canonical_structure_items(expr),
        "summary": structure_summary(expr),
    }


def _payload_sha(payload: dict) -> str:
    return sha256_text(canonical_json(payload))


# Child script: rebuilds the SAME expression deterministically and prints
# the ordered payload + its content hash as one JSON line.
_CHILD_SOURCE = '''
import json
import sympy
from symbolic_compactification import (
    canonical_json, canonical_structure_items, ordered_atoms, sha256_text,
    structure_summary)

n, k = sympy.symbols("n k", real=True)
N, M = sympy.symbols("N M", real=True)
x = sympy.Symbol("x", real=True)
f, g, h = sympy.Function("f"), sympy.Function("g"), sympy.Function("h")
expr = (
    sympy.Sum(f(n) * g(n), (n, 1, N))
    + sympy.Sum(h(k), (k, 0, M))
    + sympy.Sum(n**2, (n, 1, N))
    + sympy.Piecewise((x, x > 0), (-x, x < 0), (0, True))
    + sympy.Piecewise((f(n), n >= 1), (0, True))
    + sympy.Product(f(n), (n, 1, N))
)
payload = {
    "atoms": [sympy.srepr(a) for a in ordered_atoms(expr)],
    "sums_atoms": [sympy.srepr(a) for a in ordered_atoms(expr, sympy.Sum)],
    "items": canonical_structure_items(expr),
    "summary": structure_summary(expr),
}
print(json.dumps({"sha256": sha256_text(canonical_json(payload)),
                  "payload": payload}))
'''


def _run_child(seed: str) -> dict:
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = seed
    env["PYTHONPATH"] = _SRC + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD_SOURCE],
        capture_output=True, text=True, timeout=60, env=env)
    assert proc.returncode == 0, f"seed={seed}: {proc.stderr}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def child_results() -> dict:
    """One fresh subprocess per hash seed, shared by every cross-process
    test in this module (keeps the total subprocess runtime modest)."""
    return {seed: _run_child(seed) for seed in _HASH_SEEDS}


# --------------------------------------------------------------------------- #
# (a) in-process stability
# --------------------------------------------------------------------------- #

def test_ordered_atoms_is_sorted_by_srepr_and_repeatable():
    expr = _build_heavy_expression()
    atoms = ordered_atoms(expr)
    assert atoms, "the heavy fixture must have atoms"
    # explicit sort key: canonical srepr (hash-seed independent)
    assert [sympy.srepr(a) for a in atoms] == sorted(
        sympy.srepr(a) for a in atoms)
    # repeated calls in the same process are identical
    for _ in range(5):
        assert [sympy.srepr(a) for a in ordered_atoms(expr)] == \
            [sympy.srepr(a) for a in atoms]


def test_canonical_structure_items_stable_and_json_serializable():
    expr = _build_heavy_expression()
    items = canonical_structure_items(expr)
    # JSON-serializable by construction (json.dumps must not raise)
    json.dumps(items)
    assert set(items) == {"sums", "products", "piecewise",
                          "free_symbols", "indexed_names"}
    # every list is explicitly sorted (srepr / name order)
    for key in ("sums", "products", "piecewise"):
        assert items[key] == sorted(items[key]), key
        assert items[key], f"{key} must be non-empty for the heavy fixture"
    assert items["free_symbols"] == sorted(items["free_symbols"])
    assert items["indexed_names"] == ["f", "g", "h"]
    for _ in range(5):
        assert canonical_structure_items(expr) == items


# --------------------------------------------------------------------------- #
# (b) cross-process identity under DIFFERENT PYTHONHASHSEED values
# --------------------------------------------------------------------------- #

def test_ordered_payload_identical_across_hash_seeds(child_results):
    """The anti-regression itself: >=3 fresh processes with different hash
    seeds must produce the IDENTICAL ordered lists and content hash."""
    reference = _ordered_payload(_build_heavy_expression())
    reference_sha = _payload_sha(reference)

    seen_shas = set()
    for seed, child in child_results.items():
        assert child["sha256"] == reference_sha, (
            f"PYTHONHASHSEED={seed} changed the structural payload hash: "
            "some engine path iterates an unordered set")
        assert child["payload"] == reference, \
            f"PYTHONHASHSEED={seed} changed the ordered structural output"
        seen_shas.add(child["sha256"])
    assert len(seen_shas) == 1


def test_structural_hash_stable_across_processes(child_results):
    """A structural hash built ONLY from the ordered helpers is reproducible
    across processes (the hash a raw ``.atoms()`` iteration would not be)."""
    expr = _build_heavy_expression()
    structural_hash = sha256_text(canonical_json({
        "items": canonical_structure_items(expr),
        "atoms": [sympy.srepr(a) for a in ordered_atoms(expr)],
    }))
    for seed, child in child_results.items():
        child_hash = sha256_text(canonical_json({
            "items": child["payload"]["items"],
            "atoms": child["payload"]["atoms"],
        }))
        assert child_hash == structural_hash, f"seed={seed}"


# --------------------------------------------------------------------------- #
# (c) the helpers feed the structure summaries
# --------------------------------------------------------------------------- #

def test_structure_summary_consistent_with_canonical_items():
    """structure_summary's counts are exactly the canonical ordered item
    counts (the summary consumes the deterministic helpers)."""
    expr = _build_heavy_expression()
    items = canonical_structure_items(expr)
    summary = structure_summary(expr)
    assert summary["sums"] == len(items["sums"]) == 3
    assert summary["products"] == len(items["products"]) == 1
    assert summary["piecewise"] == len(items["piecewise"]) == 2
    assert summary["piecewise_branches"] == 5  # 3 + 2 branches
    assert summary["free_symbols"] == items["free_symbols"]
    assert summary["indexed_names"] == items["indexed_names"]


def test_summary_hash_equal_across_processes(child_results):
    """The structure summary of the same expression hashes identically in
    every child process (part of the cross-process payload comparison)."""
    local_sha = sha256_text(
        canonical_json(structure_summary(_build_heavy_expression())))
    for seed, child in child_results.items():
        child_sha = sha256_text(canonical_json(child["payload"]["summary"]))
        assert child_sha == local_sha, f"seed={seed}"
