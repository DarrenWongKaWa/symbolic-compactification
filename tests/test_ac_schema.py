"""Assumption-complete IR. Guo is not an admitted DEV/TEST case."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.schema import (  # noqa: E402
    CandidateDossier,
    DECLARED,
    NOT_DECLARED,
    Predicate,
    ScientificAssumptionContract,
    guo_is_not_admitted,
)


def test_not_declared_analytic_is_underspecified():
    ac = ScientificAssumptionContract(
        analytic_domains=[Predicate("z not a pole", NOT_DECLARED)],
        source_provenance=["placeholder"],
    )
    assert ac.has_not_declared_analytic() is True
    ac2 = ScientificAssumptionContract(
        analytic_domains=[Predicate("z not a pole", DECLARED, "source §1")],
    )
    assert ac2.has_not_declared_analytic() is False


def test_guo_dossier_is_not_admitted():
    g = CandidateDossier(
        case_id="guo-sigma-abc",
        title="Guo sigma_abc",
        domain="thermal",
        expression_sketch="...",
        latent_structure="DD",
        is_guo=True,
    )
    assert guo_is_not_admitted(g) is False
    ok = CandidateDossier(
        case_id="resolvent-dd-01",
        title="matrix resolvent divided difference",
        domain="mathphys",
        expression_sketch="(f(A)-f(B))/(A-B)",
        latent_structure="Newton DD of matrix function",
    )
    assert guo_is_not_admitted(ok) is True
