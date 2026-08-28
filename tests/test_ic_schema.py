"""Track V3 IteratedConfluenceCertificate contract."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.schema import (  # noqa: E402
    CONSISTENT_ZERO,
    CONSISTENCY_UNKNOWN,
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    INCONSISTENT_NONZERO,
    PATH_NONZERO,
    PATH_UNKNOWN,
    PATH_ZERO,
    compose_family_verdict,
    compose_path_verdict,
)


def test_empty_path_is_unknown_not_zero():
    assert compose_path_verdict([]) == PATH_UNKNOWN


def test_path_all_zero():
    assert compose_path_verdict(["ZERO", "ZERO"]) == PATH_ZERO


def test_path_any_nonzero():
    assert compose_path_verdict(["ZERO", "NONZERO"]) == PATH_NONZERO


def test_path_unknown_blocks_path_zero():
    assert compose_path_verdict(["ZERO", "UNKNOWN"]) == PATH_UNKNOWN


def test_path_zero_is_not_family_zero():
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO],
            consistency_verdicts=[],
            reconstruction_verdicts=["ZERO"],
            require_path_independence=True,
        )
        == FAMILY_UNKNOWN
    )


def test_majority_paths_not_family_zero():
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO, PATH_ZERO, PATH_UNKNOWN],
            consistency_verdicts=[CONSISTENT_ZERO],
            reconstruction_verdicts=["ZERO"],
            require_path_independence=True,
        )
        == FAMILY_UNKNOWN
    )


def test_order_dependent_never_family_zero():
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO, PATH_ZERO],
            consistency_verdicts=[INCONSISTENT_NONZERO],
            reconstruction_verdicts=["ZERO"],
            require_path_independence=True,
        )
        == FAMILY_NONZERO
    )
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO, PATH_ZERO],
            consistency_verdicts=[CONSISTENCY_UNKNOWN],
            reconstruction_verdicts=["ZERO"],
            require_path_independence=True,
        )
        == FAMILY_UNKNOWN
    )


def test_family_zero_needs_consistency_when_required():
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO, PATH_ZERO],
            consistency_verdicts=[CONSISTENT_ZERO],
            reconstruction_verdicts=["ZERO"],
            required_edge_verdicts=["ZERO", "ZERO"],
            require_path_independence=True,
        )
        == FAMILY_ZERO
    )


def test_any_nonzero_edge_is_family_nonzero():
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO],
            consistency_verdicts=[CONSISTENT_ZERO],
            reconstruction_verdicts=["ZERO"],
            required_edge_verdicts=["ZERO", "NONZERO"],
            require_path_independence=True,
        )
        == FAMILY_NONZERO
    )


def test_single_path_family_without_independence():
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO],
            consistency_verdicts=[],
            reconstruction_verdicts=["ZERO"],
            required_edge_verdicts=["ZERO"],
            require_path_independence=False,
        )
        == FAMILY_ZERO
    )
