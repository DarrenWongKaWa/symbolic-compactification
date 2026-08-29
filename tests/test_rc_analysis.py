"""Affine holomorphic Taylor remainder hypotheses. CERTIFIED is not hop ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.analysis import (  # noqa: E402
    CLASSICAL_EXCLUDED_POINTS,
    ENTIRE_FAMILIES,
    H1_HOLOMORPHIC_DISK,
    H5_NO_CLASS_CD,
    H7_SINGULARITY_AT_EXPANSION,
    HOLOMORPHY_DECLARED_DISK,
    HOLOMORPHY_GENERICITY,
    T1_HOLOMORPHIC_TAYLOR,
    T2_CAUCHY_ESTIMATES,
    T7_AFFINE_HOLOMORPHIC_REMAINDER,
    THEOREM_IDS,
    VERIFIER_CHECKS,
    CauchyBoundRequest,
    affine_path,
    affine_taylor_remainder_certificate,
    cauchy_bound_request,
    collect_affine_remainder_hypotheses,
    distance_to_singularity,
    exists_positive_staying_delta,
    holomorphic_disk,
    integral_remainder_applicable,
    lagrange_remainder_applicable,
    open_disk_radius_from_distance,
    path_stays_inside,
    remainder_order_big_o,
    staying_delta,
)
from research.remainder_certification.schema import (  # noqa: E402
    ASSUMPTION_REQUIRED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    NEIGHBORHOOD_CERTIFIED,
    NONANALYTIC,
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

PKG = ROOT / "research" / "remainder_certification" / "analysis"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "PhiGamma")
HYP = PKG / "hypotheses.py"
THM = PKG / "THEOREMS.md"


def test_public_api():
    assert callable(holomorphic_disk)
    assert callable(path_stays_inside)
    assert callable(affine_taylor_remainder_certificate)
    assert T7_AFFINE_HOLOMORPHIC_REMAINDER in THEOREM_IDS
    assert H1_HOLOMORPHIC_DISK in VERIFIER_CHECKS
    assert "exp" in ENTIRE_FAMILIES
    sig = inspect.signature(holomorphic_disk)
    assert "z0" in sig.parameters and "rho" in sig.parameters
    sig_p = inspect.signature(path_stays_inside)
    for name in ("z0", "c", "delta", "rho"):
        assert name in sig_p.parameters


def test_holomorphic_disk_positive_radius():
    disk = holomorphic_disk(0, 1)
    assert disk.well_formed is True
    assert disk.rho_positive is True
    assert disk.may_certify is True
    assert disk.source == HOLOMORPHY_DECLARED_DISK


def test_holomorphic_disk_rejects_nonpositive_and_floats():
    assert holomorphic_disk(0, 0).may_certify is False
    assert holomorphic_disk(0, 0).rho_positive is False
    assert holomorphic_disk(0, -1).may_certify is False
    assert holomorphic_disk(0, 1.5).well_formed is False
    assert holomorphic_disk(0, 1, source=HOLOMORPHY_GENERICITY).may_certify is False


def test_path_stays_inside_numeric():
    ok = path_stays_inside(0, 1, sympy.Rational(1, 2), 1)
    assert ok.holds is True
    bad = path_stays_inside(0, 1, 2, 1)
    assert bad.holds is False
    point = path_stays_inside(3, 0, 10, 1)
    assert point.holds is True


def test_path_stays_inside_unknown_and_nonpositive_delta():
    c = sympy.Symbol("c")
    unknown = path_stays_inside(0, c, 1, 1)
    assert unknown.holds is None
    assert path_stays_inside(0, 1, 0, 1).holds is False
    assert path_stays_inside(0, 1, -1, 2).holds is False


def test_witness_delta_stays_inside_for_symbolic_c():
    c = sympy.Symbol("c")
    rho = sympy.Integer(2)
    delta = staying_delta(c, rho)
    assert delta is not None
    assert exists_positive_staying_delta(c, rho) is True
    stays = path_stays_inside(0, c, delta, rho)
    assert stays.holds is True


def test_entire_exp_symbolic_parameters_certified():
    z0, c = sympy.symbols("z0 c")
    cert = affine_taylor_remainder_certificate(
        function_family="exp", z0=z0, c=c, N=3
    )
    assert validate_certificate(cert) == CERTIFIED
    assert cert.verdict == CERTIFIED
    assert "entire" in cert.domain_conditions
    assert remainder_order_big_o(3) in cert.remainder_form
    assert cert.required_small_t_condition
    assert cert.bound == ""
    assert cert.neighborhood_verdict == NEIGHBORHOOD_CERTIFIED
    assert T7_AFFINE_HOLOMORPHIC_REMAINDER in cert.proof_dependencies
    assert T1_HOLOMORPHIC_TAYLOR in cert.proof_dependencies
    assert cert.verdict != HOP_ZERO
    assert remainder_cannot_be_hop_zero(cert.verdict)


def test_class_c_genericity_is_assumption_required():
    cert = affine_taylor_remainder_certificate(
        function_family="exp",
        z0=sympy.Symbol("z0"),
        c=1,
        N=1,
        assumptions_used=[
            {"class": C_GENERICITY, "predicate": "z0 not a pole (genericity)"}
        ],
    )
    assert cert.verdict == ASSUMPTION_REQUIRED
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED
    assert cert.verdict != CERTIFIED
    hyp = collect_affine_remainder_hypotheses(
        function_family="log",
        z0=sympy.Symbol("z0"),
        c=1,
        N=1,
        rho=1,
        holomorphy_source=HOLOMORPHY_GENERICITY,
    )
    assert hyp.verdict == ASSUMPTION_REQUIRED
    assert H5_NO_CLASS_CD in hyp.failed_checks


def test_class_d_cannot_certify():
    cert = affine_taylor_remainder_certificate(
        function_family="exp",
        z0=0,
        c=1,
        N=0,
        assumptions_used=[{"class": D_HUMAN_REQUIRED, "predicate": "beta > 0"}],
    )
    assert cert.verdict == ASSUMPTION_REQUIRED


def test_certified_remainder_is_not_hop_zero():
    cert = affine_taylor_remainder_certificate(
        function_family="sin", z0=0, c=1, N=2
    )
    assert cert.verdict == CERTIFIED
    assert CERTIFIED != ZERO
    assert CERTIFIED != HOP_ZERO
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
    assert remainder_cannot_be_hop_zero(cert.verdict)


def test_empty_disk_or_distance_zero_is_nonanalytic():
    z0 = sympy.Integer(0)
    cert0 = affine_taylor_remainder_certificate(
        function_family="log", z0=z0, c=1, N=1, rho=0
    )
    assert cert0.verdict == NONANALYTIC
    dist = distance_to_singularity(z0, 0)
    assert dist.vanishing is True
    cert_d = affine_taylor_remainder_certificate(
        function_family="log",
        z0=z0,
        c=1,
        N=1,
        distance=dist,
    )
    assert cert_d.verdict == NONANALYTIC
    assert open_disk_radius_from_distance(0) is None


def test_log_pole_inside_declared_disk_is_nonanalytic():
    cert = affine_taylor_remainder_certificate(
        function_family="log", z0=0, c=1, N=2, rho=1
    )
    assert cert.verdict == NONANALYTIC
    assert 0 in CLASSICAL_EXCLUDED_POINTS["log"]


def test_log_declared_disk_away_from_zero_certified():
    cert = affine_taylor_remainder_certificate(
        function_family="log",
        z0=1,
        c=sympy.Rational(1, 10),
        N=2,
        rho=sympy.Rational(1, 2),
    )
    assert validate_certificate(cert) == CERTIFIED
    assert cert.verdict == CERTIFIED
    assert any("holomorphic_disk" in d for d in cert.domain_conditions)
    wide = affine_taylor_remainder_certificate(
        function_family="log", z0=1, c=1, N=2, rho=2
    )
    assert wide.verdict == NONANALYTIC


def test_log_symbolic_z0_without_proved_disk_not_certified():
    cert = affine_taylor_remainder_certificate(
        function_family="log", z0=sympy.Symbol("z0"), c=1, N=1
    )
    assert cert.verdict in (UNKNOWN, ASSUMPTION_REQUIRED)
    assert cert.verdict != CERTIFIED
    cert_rho = affine_taylor_remainder_certificate(
        function_family="log",
        z0=sympy.Symbol("z0"),
        c=1,
        N=1,
        rho=1,
    )
    assert cert_rho.verdict != CERTIFIED


def test_no_silent_sufficiently_small_t():
    hyp = collect_affine_remainder_hypotheses(
        function_family="exp", z0=0, c=1, N=1
    )
    assert hyp.verdict == CERTIFIED
    assert hyp.required_small_t_condition
    assert "|t|" in hyp.required_small_t_condition
    assert hyp.stays is not None and hyp.stays.holds is True


def test_missing_disk_for_non_entire_is_unknown():
    cert = affine_taylor_remainder_certificate(
        function_family="unspecified", z0=0, c=1, N=1
    )
    assert cert.verdict == UNKNOWN
    assert cert.verdict != CERTIFIED


def test_non_affine_path_unknown():
    t = sympy.Symbol("t")
    cert = affine_taylor_remainder_certificate(
        function_family="exp", z0=0, c=t, N=1, t=t
    )
    assert cert.verdict == UNKNOWN
    path = affine_path(0, t, t=t)
    assert path.affine is False


def test_negative_or_bool_order_unknown():
    assert (
        affine_taylor_remainder_certificate(
            function_family="exp", z0=0, c=1, N=-1
        ).verdict
        == UNKNOWN
    )
    assert (
        affine_taylor_remainder_certificate(
            function_family="exp", z0=0, c=1, N=True
        ).verdict
        == UNKNOWN
    )


def test_open_disk_radius_equals_positive_distance():
    d = sympy.Integer(3)
    rho = open_disk_radius_from_distance(d)
    assert rho == d
    rec = distance_to_singularity(1, d)
    cert = affine_taylor_remainder_certificate(
        function_family="unspecified",
        z0=1,
        c=1,
        N=0,
        distance=rec,
    )
    assert cert.verdict == CERTIFIED
    assert T7_AFFINE_HOLOMORPHIC_REMAINDER in cert.proof_dependencies
    assert cert.distance_to_singularity == "3"


def test_cauchy_circle_must_be_strictly_inside_and_has_no_m():
    req_none = cauchy_bound_request(0, 2, 3)
    assert req_none.M is None
    assert req_none.bound == ""
    assert req_none.well_formed is False
    assert req_none.circle_radius is None
    ok = cauchy_bound_request(0, 2, 3, r=1)
    assert ok.well_formed is True
    assert ok.M is None
    assert ok.bound == ""
    assert ok.theorem == T2_CAUCHY_ESTIMATES
    on_boundary = cauchy_bound_request(0, 2, 3, r=2)
    assert on_boundary.well_formed is False
    outside = cauchy_bound_request(0, 1, 0, r=2)
    assert outside.well_formed is False


def test_lagrange_only_on_real_segment():
    assert lagrange_remainder_applicable(t_is_real=False, segment_in_domain=True) is False
    assert lagrange_remainder_applicable(t_is_real=True, segment_in_domain=False) is False
    assert lagrange_remainder_applicable(t_is_real=True, segment_in_domain=True) is True
    assert integral_remainder_applicable(t_is_real=True, segment_in_domain=True) is True
    hyp_c = collect_affine_remainder_hypotheses(
        function_family="exp", z0=0, c=1, N=2, t_is_real=False
    )
    assert hyp_c.lagrange_ok is False
    assert "lagrange" not in hyp_c.remainder_form
    hyp_r = collect_affine_remainder_hypotheses(
        function_family="exp", z0=0, c=1, N=2, t_is_real=True
    )
    assert hyp_r.lagrange_ok is True
    assert "lagrange" in hyp_r.remainder_form
    assert "integral_real_segment" in hyp_r.remainder_form


def test_caller_delta_too_large_shrinks_to_witness():
    cert = affine_taylor_remainder_certificate(
        function_family="exp", z0=0, c=1, N=1, rho=1, delta=10
    )
    assert cert.verdict == CERTIFIED
    hyp = collect_affine_remainder_hypotheses(
        function_family="cos", z0=0, c=1, N=1, rho=1, delta=10
    )
    assert hyp.verdict == CERTIFIED
    assert hyp.stays is not None and hyp.stays.holds is True
    assert hyp.stays.delta != sympy.Integer(10)
    assert path_stays_inside(0, 1, 10, 1).holds is False


def test_infinite_c_not_certified():
    cert = affine_taylor_remainder_certificate(
        function_family="exp", z0=0, c=sympy.oo, N=1
    )
    assert cert.verdict in (UNKNOWN, NONANALYTIC)
    assert cert.verdict != CERTIFIED


def test_no_cauchy_bound_or_polygamma_locator_implementation():
    src = HYP.read_text(encoding="utf-8")
    assert "def max_modulus" not in src
    assert "def cauchy_estimate" not in src
    assert "def locate_polygamma" not in src
    assert "class CauchyBoundProvider" in src
    assert "class SingularityDistanceProvider" in src
    assert "Z_<=0" not in src
    assert "nonpositive integer" not in src
    assert CauchyBoundRequest.__dataclass_fields__["M"].default is None


def test_theorems_document_classical_sources_and_checks():
    text = THM.read_text(encoding="utf-8")
    lower = text.lower()
    for tok in (
        "ahlfors",
        "conway",
        "cauchy",
        "lagrange",
        "rudin",
        "taylor",
        "distance",
        "o(t^{n+1})",
        "not hop",
        "assumption_required",
        "genericity",
    ):
        assert tok in lower, tok
    for name in THEOREM_IDS:
        assert name in text, name
    for check in VERIFIER_CHECKS:
        assert check in text
    assert "not novelty" in lower or "not claimed as novelty" in lower
    assert "R4" in text and "R2" in text


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)


def test_hypotheses_do_not_import_hop_engine_or_v5_remainder():
    src = HYP.read_text(encoding="utf-8")
    assert "coefficient_laurent" not in src
    assert "remainder_ok" not in src
    assert "compose_hop_verdict" not in src
    assert HOP_ZERO not in (
        affine_taylor_remainder_certificate(
            function_family="exp", z0=0, c=1, N=0
        ).verdict,
    )


def test_failed_h7_recorded_on_pole_at_z0():
    hyp = collect_affine_remainder_hypotheses(
        function_family="log", z0=0, c=1, N=1, rho=1
    )
    assert hyp.verdict == NONANALYTIC
    assert H7_SINGULARITY_AT_EXPANSION in hyp.failed_checks
