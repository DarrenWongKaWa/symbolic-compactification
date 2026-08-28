"""Exact Laurent atom decomposition. Reconstruction failure is not ignored."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.atoms import (  # noqa: E402
    ReconstructionError,
    decompose,
    reconstruct,
)
import research.coefficient_laurent.atoms.core as decompose_mod  # noqa: E402
from research.coefficient_laurent.schema import (  # noqa: E402
    ATOM_CLASSES,
    LaurentAtom,
    METHOD_VERSION,
)

ATOMS_DIR = ROOT / "research" / "coefficient_laurent" / "atoms"
ATOM_MAP = ATOMS_DIR / "ATOM_MAP.json"
FREEZE = ROOT / "research" / "coefficient_laurent" / "FROZEN_INPUTS_V5.json"


def _eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        if sympy.expand(a - b) == 0:
            return True
    except Exception:
        pass
    try:
        return sympy.cancel(a - b) == 0
    except Exception:
        return False


def _pg_sum() -> tuple[sympy.Expr, sympy.Expr, sympy.Expr, sympy.Expr]:
    x, y = sympy.symbols("x y")
    K = (sympy.polygamma(0, y) - sympy.polygamma(0, x)) / (y - x)
    return x, y, K, K


def _cubic() -> tuple[sympy.Expr, sympy.Expr, sympy.Expr]:
    x, y = sympy.symbols("x y")
    return x, y, (x ** 3 - y ** 3) / (x - y)


def test_public_api_importable():
    from research.coefficient_laurent.atoms import decompose as d
    from research.coefficient_laurent.atoms import reconstruct as r
    from research.coefficient_laurent.atoms.core import decompose as d2
    from research.coefficient_laurent.atoms.core import reconstruct as r2

    assert d is d2
    assert r is r2


def test_reconstruct_decompose_polygamma_sum():
    x, y, K, _ = _pg_sum()
    out = decompose(K, y, x, "pg-sum", "hash-pg")
    assert out.reconstruction_ok is True
    assert out.note != "reconstruction_failed"
    assert len(out.atoms) == 2
    assert all(atom.atom_class == "POLYGAMMA" for atom in out.atoms)
    assert all(atom.function_head == "polygamma" for atom in out.atoms)
    rebuilt = reconstruct(out)
    assert _eq(rebuilt, K)
    assert _eq(reconstruct(out.pref, out.atoms), K)
    assert sympy.expand(rebuilt - K) == 0


def test_reconstruct_decompose_cubic():
    x, y, K = _cubic()
    out = decompose(K, y, x, "cubic", "hash-cubic")
    assert out.reconstruction_ok is True
    assert len(out.atoms) == 2
    assert {atom.atom_class for atom in out.atoms} <= {"POWER", "RATIONAL"}
    rebuilt = reconstruct(decompose(K, y, x, "cubic", "hash-cubic"))
    assert _eq(rebuilt, K)
    assert sympy.expand(rebuilt - K) == 0


def test_deterministic_ordering():
    x, y = sympy.symbols("x y")
    a = sympy.polygamma(1, y)
    b = sympy.polygamma(0, x)
    left = sympy.Add(a, b, evaluate=False)
    right = sympy.Add(b, a, evaluate=False)
    d1 = decompose(left, y, x, "ord", "h")
    d2 = decompose(right, y, x, "ord", "h")
    d3 = decompose(left, y, x, "ord", "h")
    h1 = [atom.canonical_atom_hash for atom in d1.atoms]
    h2 = [atom.canonical_atom_hash for atom in d2.atoms]
    h3 = [atom.canonical_atom_hash for atom in d3.atoms]
    assert h1 == h2 == h3
    assert [atom.atom_id for atom in d1.atoms] == [atom.atom_id for atom in d2.atoms]
    assert d1.atom_decomposition_hash == d2.atom_decomposition_hash == d3.atom_decomposition_hash
    keys = [
        (atom.atom_class, atom.function_head, atom.function_order, atom.argument, atom.coefficient)
        for atom in d1.atoms
    ]
    assert keys == sorted(keys)


def test_spectator_pref_reconstruct():
    x, y, m = sympy.symbols("x y m")
    h1 = sympy.Function("h1")
    kernel = (sympy.polygamma(0, y) + sympy.polygamma(0, x)) / (y - x)
    expr = h1(m) * kernel
    out = decompose(expr, y, x, "spec", "h")
    assert out.reconstruction_ok is True
    assert out.spectator == h1(m)
    assert _eq(reconstruct(out), expr)
    assert all(atom.spectator == str(h1(m)) for atom in out.atoms)


def test_each_atom_at_most_one_polygamma():
    x, y, K, _ = _pg_sum()
    out = decompose(K, y, x, "pg-sum", "hash-pg")
    for atom in out.atoms:
        term = reconstruct(sympy.Integer(1), [atom])
        assert len(term.atoms(sympy.polygamma)) <= 1


def test_reconstruction_failure_not_silently_ignored(monkeypatch):
    x, y, K, _ = _pg_sum()

    real_split = decompose_mod._split_pref_add

    def lie(expr):
        _pref, add, _ok = real_split(expr)
        return sympy.Integer(2), add, True

    monkeypatch.setattr(decompose_mod, "_split_pref_add", lie)
    out = decompose(K, y, x, "pg-sum", "hash-pg")
    assert out.reconstruction_ok is False
    assert out.note == "reconstruction_failed"
    rebuilt = reconstruct(out)
    assert not _eq(rebuilt, K)
    assert rebuilt != K


def test_reconstruct_raises_on_bad_atom():
    with pytest.raises(ReconstructionError):
        reconstruct(
            sympy.Integer(1),
            [
                LaurentAtom(
                    atom_id="bad",
                    source_member="x",
                    function_head="polygamma",
                    coefficient="Integer(1)",
                )
            ],
        )
    with pytest.raises(ReconstructionError):
        reconstruct(sympy.Integer(1), ["not-an-atom"])


def test_source_ban_no_gold_pairing_or_together():
    for path in sorted(ATOMS_DIR.glob("*.py")):
        src = path.read_text()
        assert "Phi_Gamma" not in src
        assert "PhiGamma" not in src
        assert "pairing_table" not in src
        assert "PAIRING" not in src
        assert "def L4" not in src
        assert "def L5" not in src
        assert "guo pairing" not in src.lower()
        assert "sympy.simplify" not in src
    core = (ATOMS_DIR / "core.py").read_text()
    assert "together(" not in core
    assert "guo_map" not in core
    assert "limit(" not in core
    assert "ZERO" not in core or "hop ZERO" in core


def test_atom_map_frozen_hops_evaluation_only():
    assert ATOM_MAP.is_file()
    blob = json.loads(ATOM_MAP.read_text())
    freeze = json.loads(FREEZE.read_text())
    assert blob["does_not_adjudicate_zero"] is True
    assert blob["no_llm_calls"] is True
    assert blob["used_full_together"] is False
    assert blob["method_version"] == METHOD_VERSION
    assert blob["n_hops"] == freeze["n_hops"] == 18
    assert blob["n_reconstruction_ok"] == 18
    assert blob["primary_hop"] == freeze["primary_hop"]
    freeze_ids = [h["hop_id"] for h in freeze["hops"]]
    map_ids = [h["hop_id"] for h in blob["hops"]]
    assert map_ids == freeze_ids
    dumped = json.dumps(blob)
    assert '"verdict": "ZERO"' not in dumped
    assert '"final_verdict"' not in dumped
    primary = next(h for h in blob["hops"] if h.get("is_primary"))
    assert primary["source_member"] == "G0016"
    assert primary["target_member"] == "G0013"
    assert primary["reconstruction_ok"] is True
    assert primary["n_atoms"] == 14
    assert primary["atom_classes"].get("POLYGAMMA") == 14
    assert primary["source_text_hash"] == freeze["hops"][0]["source"]["text_sha256"]
    for hop in blob["hops"]:
        assert hop["reconstruction_ok"] is True
        assert hop["n_atoms"] >= 1
        assert len(hop["atom_decomposition_hash"]) == 64
        assert hop.get("verdict") not in {"ZERO", "NONZERO"}
        hashes = []
        for atom in hop["atoms"]:
            assert atom["atom_class"] in ATOM_CLASSES
            assert len(atom["canonical_atom_hash"]) == 64
            hashes.append(atom["canonical_atom_hash"])
            if atom["atom_class"] == "POLYGAMMA":
                assert atom["function_head"] == "polygamma"
        assert len(set(hashes)) == len(hashes)
        atom_ids = [a["atom_id"] for a in hop["atoms"]]
        assert atom_ids == sorted(atom_ids)


def test_atom_map_matches_live_primary_reconstruct():
    from research.llm_abstraction.constructor import parse_flex
    from research.llm_abstraction.tasks import load_guo_item

    blob = json.loads(ATOM_MAP.read_text())
    mmap = json.loads(
        (
            ROOT
            / "research"
            / "scalable_verification"
            / "guo_map"
            / "GUO_OBLIGATION_MAP.json"
        ).read_text()
    )
    primary = next(h for h in blob["hops"] if h.get("is_primary"))
    row = next(
        h
        for h in mmap["hypotheses"]
        if h.get("seed") == primary["seed"] and h.get("index") == primary["index"]
    )
    members = {m["member_id"]: m for m in row["members"]}
    item = load_guo_item()
    src = parse_flex(members[primary["source_member"]]["text"], item["symbols"], item["functions"])
    tgt = parse_flex(members[primary["target_member"]]["text"], item["symbols"], item["functions"])
    out = decompose(
        src,
        primary["degeneration_variable"],
        primary["target_value"],
        primary["source_member"],
        primary["source_text_hash"],
        partner=tgt,
    )
    assert out.reconstruction_ok is True
    assert _eq(reconstruct(out), src)
    assert out.atom_decomposition_hash == primary["atom_decomposition_hash"]
    assert [a.canonical_atom_hash for a in out.atoms] == [
        a["canonical_atom_hash"] for a in primary["atoms"]
    ]
