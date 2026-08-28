"""Reproduce the V4 cache failure: missing text_sha256 must not alias hops."""
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


def test_empty_text_refused():
    with pytest.raises(ValueError):
        member_text_hash({"member_id": "G0016", "text_sha256": ""}, text="")


def test_missing_text_sha256_hashes_full_text():
    text = "polygamma(2, z) / (eps_m - eps_n)"
    h = member_text_hash({"member_id": "G0016"}, text=text)
    assert h == sha256_text(text)


def test_stored_hash_mismatch_uses_canonical_text():
    text = "real-kernel"
    bogus = {"text_sha256": "0" * 64, "text": text}
    assert member_text_hash(bogus, text=text) == sha256_text(text)


def test_g0014_certificate_not_reused_for_g0016():
    """V4 bug: (None, None, epsilon(m), epsilon(n)) aliased distinct hops."""
    k14 = certificate_key(
        source_text="G0014-kernel-text",
        target_text="G0012-kernel-text",
        degeneration_variable="epsilon(m)",
        target_value="epsilon(n)",
        source_member={"text_sha256": ""},
        target_member={"text_sha256": ""},
        atom_decomposition_hash="atoms-14",
    )
    k16 = certificate_key(
        source_text="G0016-kernel-text",
        target_text="G0013-kernel-text",
        degeneration_variable="epsilon(m)",
        target_value="epsilon(n)",
        source_member={"text_sha256": ""},
        target_member={"text_sha256": ""},
        atom_decomposition_hash="atoms-16",
    )
    assert k14 != k16
    cache = CertificateCache()
    cache.put(k14, {"verdict": "ZERO", "hop": "G0014->G0012"})
    assert cache.get(k16) is None
    cache.put(k16, {"verdict": "UNKNOWN", "hop": "G0016->G0013"})
    assert cache.get(k14)["hop"] == "G0014->G0012"
    assert cache.get(k16)["hop"] == "G0016->G0013"


def test_same_var_same_count_different_text_distinct():
    a = certificate_key(
        source_text="expr-A",
        target_text="tgt",
        degeneration_variable="epsilon(m)",
        target_value="epsilon(n)",
        atom_decomposition_hash="12-atoms",
    )
    b = certificate_key(
        source_text="expr-B",
        target_text="tgt",
        degeneration_variable="epsilon(m)",
        target_value="epsilon(n)",
        atom_decomposition_hash="12-atoms",
    )
    assert a != b


def test_reordered_atom_hash_changes_key():
    a = certificate_key(
        source_text="same",
        target_text="tgt",
        degeneration_variable="t",
        target_value="0",
        atom_decomposition_hash="h1",
    )
    b = certificate_key(
        source_text="same",
        target_text="tgt",
        degeneration_variable="t",
        target_value="0",
        atom_decomposition_hash="h2",
    )
    assert a != b
