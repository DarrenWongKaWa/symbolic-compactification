"""RemainderCertificate IR. CERTIFIED is not hop ZERO. Domain required."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.schema import (  # noqa: E402
    ASSUMPTION_REQUIRED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    NONANALYTIC,
    RemainderCertificate,
    UNKNOWN,
    remainder_cannot_be_hop_zero,
    validate_certificate,
)
from research.coefficient_laurent.schema import (  # noqa: E402
    LEVEL_B,
    ZERO,
    compose_hop_verdict,
)
from research.coefficient_laurent.schema import UNKNOWN as HOP_UNKNOWN  # noqa: E402


def test_certified_remainder_is_not_hop_zero():
    cert = RemainderCertificate(
        function_family="exp",
        domain_conditions=["entire"],
        verdict=CERTIFIED,
    )
    assert validate_certificate(cert) == CERTIFIED
    assert remainder_cannot_be_hop_zero(cert.verdict)
    assert cert.verdict != HOP_ZERO
    assert CERTIFIED != ZERO


def test_empty_domain_conditions_not_certified():
    cert = RemainderCertificate(verdict=CERTIFIED, domain_conditions=[])
    assert validate_certificate(cert) == UNKNOWN


def test_class_c_cannot_be_certified():
    cert = RemainderCertificate(
        domain_conditions=["alpha_0 not a pole (genericity)"],
        assumptions_used=[{"class": C_GENERICITY, "predicate": "alpha_0 not in Z_<=0"}],
        verdict=CERTIFIED,
    )
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED


def test_class_d_cannot_be_certified():
    cert = RemainderCertificate(
        domain_conditions=["human physics bound"],
        assumptions_used=[{"class": D_HUMAN_REQUIRED, "predicate": "beta > 0"}],
        verdict=CERTIFIED,
    )
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED


def test_forbidden_ignore_remainder_regression():
    """LEVEL B coefficients + remainder UNKNOWN is never hop ZERO."""
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=HOP_UNKNOWN,
    )
    assert v == HOP_UNKNOWN
    assert v != ZERO
    assert lvl == LEVEL_B


def test_nonanalytic_and_unknown_are_not_zero():
    for v in (NONANALYTIC, UNKNOWN, ASSUMPTION_REQUIRED):
        cert = RemainderCertificate(domain_conditions=["stated"], verdict=v)
        assert validate_certificate(cert) == v
        assert remainder_cannot_be_hop_zero(v)
