"""Cauchy remainder order bound. CERTIFIED is not hop ZERO. No invented disk."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.cauchy import (  # noqa: E402
    CAUCHY_BOUND_FORM,
    M_FINITE_LEMMA,
    Q_FORM,
    cauchy_remainder_bound,
)
from research.remainder_certification.schema import (  # noqa: E402
    ASSUMPTION_REQUIRED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    NEIGHBORHOOD_CERTIFIED,
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
import research.remainder_certification.cauchy as cauchy_pkg  # noqa: E402
import research.remainder_certification.cauchy.bound as bound_mod  # noqa: E402

PKG = ROOT / "research" / "remainder_certification" / "cauchy"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "PhiGamma", "G0016", "G0013")


def _disk(rho, z0=0, family="exp", **extra):
    payload = {
        "verdict": NEIGHBORHOOD_CERTIFIED,
        "radius": rho,
        "center": z0,
        "function_family": family,
        "domain_conditions": ["entire"] if family == "exp" else [f"pole-free disk rho={rho}"],
    }
    payload.update(extra)
    return payload


def test_public_api():
    assert callable(cauchy_remainder_bound)
    assert cauchy_pkg.cauchy_remainder_bound is cauchy_remainder_bound
    sig = inspect.signature(cauchy_remainder_bound)
    assert "neighborhood" in sig.parameters
    assert "N" in sig.parameters
    assert "r" in sig.parameters
    assert CAUCHY_BOUND_FORM == "M * q(t)**(N+1)"
    assert Q_FORM == "|c|*|t|/r"
    assert "compact" in M_FINITE_LEMMA.lower()
    assert CERTIFIED != HOP_ZERO
    assert CERTIFIED != ZERO


def test_readme_does_not_claim_a_disk():
    text = (PKG / "README.md").read_text(encoding="utf-8").lower()
    for tok in (
        "does **not** certify a disk",
        "missing neighborhood is `unknown`",
        "m < infinity",
        "o(t",
        "certified_neighborhood",
        "not hop",
        "d2",
        "exp",
    ):
        assert tok in text, tok
    assert "r >= rho" in text or "r >= `rho`" in text


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
        if path.suffix == ".py":
            assert "sympy.limit" not in src
            assert "remainder_certification.neighborhood" not in src


def test_exp_on_any_certified_disk():
    t = sympy.symbols("t")
    for rho in (1, 2, 5, 10):
        r = sympy.Rational(rho, 2)
        cert = cauchy_remainder_bound(
            _disk(rho),
            N=3,
            r=r,
            c=1,
            t=t,
            z0=0,
            function_family="exp",
        )
        assert cert.verdict == CERTIFIED, (rho, cert.note)
        assert validate_certificate(cert) == CERTIFIED
        assert cert.neighborhood_verdict == NEIGHBORHOOD_CERTIFIED
        assert cert.expansion_order == 3
        assert cert.bound
        assert "**(4)" in cert.bound
        assert "M" in cert.bound
        assert cert.remainder_form.startswith("|R_3(t)|")
        assert cert.analyticity_certificate.get("M_finite") is True
        assert cert.analyticity_certificate.get("does_not_claim_disk") is True
        assert cert.analyticity_certificate.get("order") == "O(t**4)"
        assert Q_FORM in (
            cert.analyticity_certificate.get("q"),
            cert.analyticity_certificate.get("q_alt"),
            Q_FORM,
        )
        assert cert.analyticity_certificate.get("q") == Q_FORM
        assert M_FINITE_LEMMA in cert.domain_conditions
        assert any("0 < r < rho" in str(a.get("predicate")) for a in cert.assumptions_used)
        assert remainder_cannot_be_hop_zero(cert.verdict)
        assert cert.verdict != HOP_ZERO
        assert "compact" in cert.required_small_t_condition.lower() or "<" in cert.required_small_t_condition


def test_exp_default_contour_half_rho():
    cert = cauchy_remainder_bound(
        _disk(4), N=1, c=1, t="t", z0=0, function_family="exp"
    )
    assert cert.verdict == CERTIFIED
    assert cert.analyticity_certificate["r"] in ("2", "2.0")
    assert cert.expansion_order == 1
    assert "**(2)" in cert.bound


def test_exp_without_disk_is_unknown():
    cert = cauchy_remainder_bound(
        None, N=3, r=1, c=1, t="t", function_family="exp"
    )
    assert cert.verdict == UNKNOWN
    assert cert.verdict != CERTIFIED
    assert "does not invent a disk" in cert.note.lower() or "missing" in cert.note.lower()


def test_missing_disk_unknown():
    cases = [
        None,
        {},
        {"radius": 2},
        {"verdict": UNKNOWN, "radius": 2},
        {"verdict": "UNSUPPORTED", "radius": 2},
        {"neighborhood_verdict": UNKNOWN, "rho": 3},
    ]
    n_cert = 0
    for nb in cases:
        cert = cauchy_remainder_bound(nb, N=2, r=1, c=1, t="t")
        assert cert.verdict != CERTIFIED, nb
        assert cert.verdict == UNKNOWN
        n_cert += int(cert.verdict == CERTIFIED)
    assert n_cert == 0


def test_r_ge_rho_unknown():
    equal = cauchy_remainder_bound(_disk(1), N=2, r=1, c=1, t="t", function_family="exp")
    outside = cauchy_remainder_bound(_disk(1), N=2, r=2, c=1, t="t", function_family="exp")
    for cert, label in ((equal, "equal"), (outside, "outside")):
        assert cert.verdict == UNKNOWN, label
        assert cert.verdict != CERTIFIED
        assert "r" in cert.note.lower()
    # neighborhood was certified; the contour is the failure
    assert equal.neighborhood_verdict == NEIGHBORHOOD_CERTIFIED


def test_n_missing_unknown():
    cert = cauchy_remainder_bound(_disk(2), r=1, c=1, t="t", function_family="exp")
    assert cert.verdict == UNKNOWN
    assert cert.verdict != CERTIFIED
    assert cert.expansion_order is None
    neg = cauchy_remainder_bound(_disk(2), N=-1, r=1, c=1, t="t")
    assert neg.verdict == UNKNOWN
    blank = cauchy_remainder_bound(_disk(2), N="", r=1, c=1, t="t")
    assert blank.verdict == UNKNOWN


def test_certified_remainder_is_not_hop_zero():
    cert = cauchy_remainder_bound(
        _disk(2), N=0, r=1, c=1, t="t", function_family="exp"
    )
    assert cert.verdict == CERTIFIED
    assert cert.verdict != HOP_ZERO
    assert cert.verdict != ZERO
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=cert.verdict,
    )
    assert v == HOP_UNKNOWN
    assert v != ZERO
    assert lvl == LEVEL_B


def test_m_finite_lemma_required():
    cert = cauchy_remainder_bound(
        _disk(3), N=4, r=1, c=1, t="t", function_family="exp"
    )
    assert cert.verdict == CERTIFIED
    assert cert.analyticity_certificate["M_finiteness"] == M_FINITE_LEMMA
    blob = " ".join(cert.proof_dependencies).lower()
    assert "compact" in blob or "bounded" in blob
    inf = cauchy_remainder_bound(
        _disk(3), N=4, r=1, c=1, t="t", function_family="exp", M=sympy.oo
    )
    assert inf.verdict != CERTIFIED
    assert inf.verdict in (UNKNOWN, ASSUMPTION_REQUIRED)


def test_assumption_required_neighborhood():
    nb = {
        "verdict": ASSUMPTION_REQUIRED,
        "radius": 2,
        "function_family": "exp",
        "assumptions_used": [
            {"class": C_GENERICITY, "predicate": "generic pole-free disk"}
        ],
    }
    cert = cauchy_remainder_bound(nb, N=2, r=1, c=1, t="t")
    assert cert.verdict == ASSUMPTION_REQUIRED
    assert cert.verdict != CERTIFIED
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED


def test_class_c_cannot_be_certified():
    cert = cauchy_remainder_bound(
        _disk(2),
        N=2,
        r=1,
        c=1,
        t="t",
        function_family="exp",
        assumptions_used=[
            {"class": C_GENERICITY, "predicate": "M < infinity by genericity"}
        ],
    )
    assert cert.verdict == ASSUMPTION_REQUIRED
    assert cert.verdict != CERTIFIED
    d = cauchy_remainder_bound(
        _disk(2),
        N=2,
        r=1,
        c=1,
        t="t",
        function_family="exp",
        assumptions_used=[
            {"class": D_HUMAN_REQUIRED, "predicate": "physics bound on M"}
        ],
    )
    assert d.verdict == ASSUMPTION_REQUIRED
    assert d.verdict != CERTIFIED


def test_unproved_r_lt_rho_unknown():
    r, rho = sympy.symbols("r rho")
    cert = cauchy_remainder_bound(
        _disk(rho), N=1, r=r, c=1, t="t", function_family="exp"
    )
    assert cert.verdict == UNKNOWN
    assert cert.verdict != CERTIFIED


def test_float_radius_unknown():
    cert = cauchy_remainder_bound(
        _disk(2.5), N=1, r=1.0, c=1, t="t", function_family="exp"
    )
    assert cert.verdict == UNKNOWN
    assert cert.verdict != CERTIFIED


def test_remainder_certificate_as_neighborhood():
    nb = RemainderCertificate(
        function_family="exp",
        expansion_point="0",
        domain_conditions=["entire"],
        analyticity_certificate={"rho": 6, "center": 0},
        distance_to_singularity="6",
        neighborhood_verdict=NEIGHBORHOOD_CERTIFIED,
        verdict=UNKNOWN,
    )
    cert = cauchy_remainder_bound(nb, N=2, r=2, c=1, t="t")
    assert cert.verdict == CERTIFIED
    assert cert.distance_to_singularity == "6"
    assert cert.function_family == "exp"


def test_c_depends_on_t_unknown():
    t = sympy.symbols("t")
    cert = cauchy_remainder_bound(
        _disk(2), N=1, r=1, c=t, t=t, function_family="exp"
    )
    assert cert.verdict == UNKNOWN
    assert cert.verdict != CERTIFIED


def test_rho_prime_alias_and_small_t_delta():
    cert = cauchy_remainder_bound(
        _disk(4), N=5, rho_prime=1, c=2, t="t", z0=1, function_family="exp"
    )
    assert cert.verdict == CERTIFIED
    assert "q_alt" in cert.analyticity_certificate
    assert "|t|" in cert.required_small_t_condition
    assert "1/|2|" in cert.required_small_t_condition.replace(" ", "") or "/|2|" in cert.required_small_t_condition or "/2" in cert.required_small_t_condition.replace(" ", "")
    assert cert.expansion_order == 5
    assert "**(6)" in cert.bound


def test_validate_never_upgrades_and_domain_nonempty():
    cert = cauchy_remainder_bound(_disk(2), N=2, r=1, function_family="exp")
    assert cert.domain_conditions
    assert validate_certificate(cert) == cert.verdict
    missing = cauchy_remainder_bound(None, N=2, r=1)
    assert missing.domain_conditions
    assert validate_certificate(missing) == UNKNOWN


def test_false_certified_is_zero_on_negatives():
    rows = [
        cauchy_remainder_bound(None, N=2, r=1, function_family="exp"),
        cauchy_remainder_bound(_disk(1), N=2, r=1, function_family="exp"),
        cauchy_remainder_bound(_disk(2), r=1, function_family="exp"),
        cauchy_remainder_bound({"verdict": UNKNOWN, "radius": 4}, N=1, r=1),
    ]
    n_false = sum(1 for c in rows if c.verdict == CERTIFIED)
    assert n_false == 0


def test_bound_module_documents_order_control():
    doc = (bound_mod.__doc__ or "").lower()
    for tok in ("o(t", "does not certify a disk", "m", "q", "certified"):
        assert tok in doc, tok
    src = (PKG / "bound.py").read_text(encoding="utf-8")
    assert "LEVEL_C ZERO" not in src or "not hop ZERO" in src
    assert "D2" in (PKG / "README.md").read_text(encoding="utf-8")
