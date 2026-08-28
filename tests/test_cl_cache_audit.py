"""Extra cache-identity attacks for Track V5 (V5-K).

Orchestrator coverage is tests/test_cl_cache.py. This module tightens the
V4 miss: empty text_sha256 plus the same degeneration must not alias
G0014-kernel and G0016-kernel even when the atom-decomposition hash also
collides (count-only, reordered, or empty).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.cache import (  # noqa: E402
    CertificateCache,
    certificate_key,
    member_text_hash,
    sha256_text,
)

VAR = "epsilon(m)"
POINT = "epsilon(n)"
MISSING = {"text_sha256": ""}
COUNT14 = "14-atoms"
G0014_KERNEL = "G0014-kernel"
G0016_KERNEL = "G0016-kernel"
G0012_KERNEL = "G0012-kernel"
G0013_KERNEL = "G0013-kernel"

ATTACK_IDS = (
    "V5K_01_missing_sha_g0014_g0016",
    "V5K_02_reordered_atoms",
    "V5K_03_changed_coefficient",
    "V5K_04_same_count_different_expression",
    "V5K_05_bogus_shared_stored_hash",
    "V5K_06_empty_atom_hash_default",
)


def _key(
    source_text: str,
    target_text: str,
    *,
    atom_decomposition_hash: str = COUNT14,
    source_member: dict | None = None,
    target_member: dict | None = None,
    degeneration_variable: str = VAR,
    target_value: str = POINT,
) -> tuple[str, ...]:
    return certificate_key(
        source_text=source_text,
        target_text=target_text,
        degeneration_variable=degeneration_variable,
        target_value=target_value,
        source_member=source_member if source_member is not None else MISSING,
        target_member=target_member if target_member is not None else MISSING,
        atom_decomposition_hash=atom_decomposition_hash,
    )


def _assert_no_alias(
    key_a: tuple[str, ...],
    key_b: tuple[str, ...],
    *,
    cert_a: dict,
    cert_b: dict,
) -> None:
    assert key_a != key_b
    cache = CertificateCache()
    cache.put(key_a, cert_a)
    assert cache.get(key_b) is None
    hit = cache.get_or_put(key_b, cert_b)
    assert hit["hop"] == cert_b["hop"]
    assert cache.get(key_a)["hop"] == cert_a["hop"]
    assert cache.get(key_b)["hop"] == cert_b["hop"]
    assert cache.get(key_a)["verdict"] == cert_a["verdict"]


def test_attack_ids_are_unique():
    assert len(ATTACK_IDS) == len(set(ATTACK_IDS))
    assert len(ATTACK_IDS) == 6


def test_v5k_01_missing_sha_same_var_point_does_not_alias_g0014_g0016():
    """V4 bug, stricter than test_cl_cache: atom-count hash also collides."""
    k14 = _key(G0014_KERNEL, G0012_KERNEL, atom_decomposition_hash=COUNT14)
    k16 = _key(G0016_KERNEL, G0013_KERNEL, atom_decomposition_hash=COUNT14)
    _assert_no_alias(
        k14,
        k16,
        cert_a={"verdict": "ZERO", "hop": "G0014->G0012"},
        cert_b={"verdict": "UNKNOWN", "hop": "G0016->G0013"},
    )


def test_v5k_02_reordered_atoms_same_count_hash_distinct():
    atoms = (
        "polygamma(2, z)/(eps_m - eps_n)",
        "polygamma(1, w)/(eps_m - eps_n)",
        "1/(eps_m - eps_n)",
    )
    src_a = " + ".join(atoms)
    src_b = " + ".join(reversed(atoms))
    assert src_a != src_b
    tgt = "polygamma(3, n)"
    # Count-only / order-insensitive decomposer hash would collide.
    k_a = _key(src_a, tgt, atom_decomposition_hash="3-atoms")
    k_b = _key(src_b, tgt, atom_decomposition_hash="3-atoms")
    _assert_no_alias(
        k_a,
        k_b,
        cert_a={"verdict": "ZERO", "hop": "order-abc"},
        cert_b={"verdict": "UNKNOWN", "hop": "order-cba"},
    )


def test_v5k_02_reordered_atom_decomposition_hash_also_distinct():
    src = "atomA + atomB"
    tgt = "diag"
    k_ab = _key(src, tgt, atom_decomposition_hash=sha256_text("atomA|atomB"))
    k_ba = _key(src, tgt, atom_decomposition_hash=sha256_text("atomB|atomA"))
    assert k_ab != k_ba


def test_v5k_03_changed_coefficient_not_aliased():
    tgt = "polygamma(3, n)"
    k2 = _key("2*polygamma(2, z)/(eps_m - eps_n)", tgt)
    k3 = _key("3*polygamma(2, z)/(eps_m - eps_n)", tgt)
    _assert_no_alias(
        k2,
        k3,
        cert_a={"verdict": "ZERO", "hop": "coeff-2"},
        cert_b={"verdict": "NONZERO", "hop": "coeff-3"},
    )


def test_v5k_04_same_member_count_different_expression():
    src_a = " + ".join(f"G0014-atom-{i}" for i in range(14))
    src_b = " + ".join(f"G0016-atom-{i}" for i in range(14))
    assert src_a.count("+") == src_b.count("+") == 13
    k_a = _key(src_a, G0012_KERNEL, atom_decomposition_hash=COUNT14)
    k_b = _key(src_b, G0013_KERNEL, atom_decomposition_hash=COUNT14)
    _assert_no_alias(
        k_a,
        k_b,
        cert_a={"verdict": "ZERO", "hop": "G0014-14atoms"},
        cert_b={"verdict": "UNKNOWN", "hop": "G0016-14atoms"},
    )


def test_v5k_05_bogus_identical_stored_hash_cannot_collapse_texts():
    bogus = {"text_sha256": "0" * 64}
    text_a = G0014_KERNEL
    text_b = G0016_KERNEL
    assert member_text_hash(bogus, text=text_a) == sha256_text(text_a)
    assert member_text_hash(bogus, text=text_b) == sha256_text(text_b)
    k_a = _key(text_a, G0012_KERNEL, source_member=bogus, target_member=bogus)
    k_b = _key(text_b, G0013_KERNEL, source_member=bogus, target_member=bogus)
    _assert_no_alias(
        k_a,
        k_b,
        cert_a={"verdict": "ZERO", "hop": "G0014->G0012"},
        cert_b={"verdict": "UNKNOWN", "hop": "G0016->G0013"},
    )


def test_v5k_06_empty_atom_hash_default_still_hashes_text():
    k14 = _key(G0014_KERNEL, G0012_KERNEL, atom_decomposition_hash="")
    k16 = _key(G0016_KERNEL, G0013_KERNEL, atom_decomposition_hash="")
    _assert_no_alias(
        k14,
        k16,
        cert_a={"verdict": "ZERO", "hop": "G0014->G0012"},
        cert_b={"verdict": "UNKNOWN", "hop": "G0016->G0013"},
    )


def test_identical_replay_is_a_cache_hit():
    k = _key(G0014_KERNEL, G0012_KERNEL)
    cache = CertificateCache()
    cache.put(k, {"verdict": "ZERO", "hop": "G0014->G0012"})
    again = certificate_key(
        source_text=G0014_KERNEL,
        target_text=G0012_KERNEL,
        degeneration_variable=VAR,
        target_value=POINT,
        source_member=MISSING,
        target_member=MISSING,
        atom_decomposition_hash=COUNT14,
    )
    assert again == k
    assert cache.get(again)["hop"] == "G0014->G0012"


def test_empty_text_still_refused_without_sha():
    with pytest.raises(ValueError, match="empty member text"):
        member_text_hash({"member_id": "G0016", "text_sha256": ""}, text="")


def test_false_alias_count_is_zero():
    pairs = [
        (
            _key(G0014_KERNEL, G0012_KERNEL),
            _key(G0016_KERNEL, G0013_KERNEL),
        ),
        (
            _key("a + b + c", "t", atom_decomposition_hash="3-atoms"),
            _key("c + b + a", "t", atom_decomposition_hash="3-atoms"),
        ),
        (
            _key("2*pg", "t"),
            _key("3*pg", "t"),
        ),
        (
            _key(" + ".join(f"u{i}" for i in range(14)), "t"),
            _key(" + ".join(f"v{i}" for i in range(14)), "t"),
        ),
    ]
    false_alias = sum(1 for a, b in pairs if a == b)
    assert false_alias == 0
