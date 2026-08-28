"""Track V5 hop verdict: LEVEL A is not ZERO."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.schema import (  # noqa: E402
    LEVEL_A,
    LEVEL_B,
    LEVEL_C,
    NONZERO,
    UNKNOWN,
    ZERO,
    compose_hop_verdict,
)


def test_atom_series_alone_is_not_zero():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=UNKNOWN,
        constant_verdict=UNKNOWN,
        remainder_verdict=UNKNOWN,
    )
    assert v == UNKNOWN
    assert lvl == LEVEL_A


def test_t0_match_with_surviving_pole_is_nonzero():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=NONZERO,
        constant_verdict=ZERO,
        remainder_verdict=ZERO,
    )
    assert v == NONZERO


def test_level_c_all_zero():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=ZERO,
    )
    assert v == ZERO
    assert lvl == LEVEL_C


def test_reconstruction_failure_unknown():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=False,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=ZERO,
    )
    assert v == UNKNOWN
