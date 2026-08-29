"""Pole-free affine neighborhood. Existence of delta, not hop ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.neighborhood import (  # noqa: E402
    ASSUMPTION_REQUIRED,
    CERTIFIED_NEIGHBORHOOD,
    EMPTY_POLE_SET,
    NEIGHBORHOOD_ASSUMPTION,
    NEIGHBORHOOD_CERTIFIED,
    NEIGHBORHOOD_UNKNOWN,
    NEIGHBORHOOD_VERDICTS,
    NONPOSITIVE_INTEGERS,
    UNKNOWN,
    NeighborhoodCertificate,
    PoleQuery,
    certify_neighborhood,
    default_pole_set,
    empty_pole_set,
    explicit_sufficient_delta,
    nonpositive_integer_poles,
)
from research.remainder_certification.schema import (  # noqa: E402
    A_DECLARED,
    B_DERIVED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    METHOD_VERSION,
    RemainderCertificate,
    validate_certificate,
)
from research.coefficient_laurent.schema import (  # noqa: E402
    LEVEL_B,
    ZERO,
    compose_hop_verdict,
)
from research.coefficient_laurent.schema import UNKNOWN as HOP_UNKNOWN  # noqa: E402
import research.remainder_certification.neighborhood.certify as nb_mod  # noqa: E402

PKG = ROOT / "research" / "remainder_certification" / "neighborhood"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "PhiGamma")


def _cert(*args, **kwargs):
    return certify_neighborhood(*args, **kwargs)


def _delta_inside(rho, c, delta) -> bool:
    gap = sympy.simplify(sympy.Abs(rho) - sympy.Abs(c) * delta)
    return gap.is_positive is True


def test_public_api_and_schema_verdicts():
    assert CERTIFIED_NEIGHBORHOOD == NEIGHBORHOOD_CERTIFIED == "CERTIFIED_NEIGHBORHOOD"
    assert ASSUMPTION_REQUIRED == NEIGHBORHOOD_ASSUMPTION == "ASSUMPTION_REQUIRED"
    assert UNKNOWN == NEIGHBORHOOD_UNKNOWN == "UNKNOWN"
    assert CERTIFIED_NEIGHBORHOOD != CERTIFIED
    assert CERTIFIED_NEIGHBORHOOD != HOP_ZERO
    assert CERTIFIED_NEIGHBORHOOD in NEIGHBORHOOD_VERDICTS
    assert callable(certify_neighborhood)
    assert callable(empty_pole_set)
    assert callable(nonpositive_integer_poles)
    assert callable(default_pole_set)
    sig = inspect.signature(certify_neighborhood)
    assert list(sig.parameters)[:2] == ["z0", "c"]
    assert "assumptions" in sig.parameters
    assert "pole_set" in sig.parameters
    assert "function_family" in sig.parameters


def test_exp_empty_pole_set_certifies_symbolic_z0():
    z0, c = sympy.symbols("z0 c")
    r = _cert(z0, c, function_family="exp")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert r.verdict != CERTIFIED
    assert r.verdict != ASSUMPTION_REQUIRED
    assert r.pole_set == EMPTY_POLE_SET
    assert "entire" in r.domain_conditions
    assert r.distance_to_singularity == "oo"
    assert r.sufficient_delta == "1"
    assert r.domain_conditions
    assert r.method_version == METHOD_VERSION
    assert not any(
        item.get("class") in (C_GENERICITY, D_HUMAN_REQUIRED)
        for item in r.assumptions_used
    )


def test_entire_string_pole_set_and_empty_callback():
    a = sympy.symbols("a")
    r1 = _cert(a, 1, pole_set="empty")
    r2 = _cert(a, 1, pole_set=empty_pole_set)
    r3 = _cert(a, 1, function_family="entire")
    for r in (r1, r2, r3):
        assert r.verdict == CERTIFIED_NEIGHBORHOOD
        assert r.pole_set == EMPTY_POLE_SET


def test_polygamma_safe_z0_one_explicit_rho():
    r = _cert(1, 1, function_family="polygamma")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert r.pole_set == NONPOSITIVE_INTEGERS
    rho = sympy.sympify(r.distance_to_singularity)
    delta = sympy.sympify(r.sufficient_delta)
    assert rho == 1
    assert sympy.simplify(delta - explicit_sufficient_delta(rho, 1)) == 0
    assert delta == sympy.Rational(1, 4)
    assert _delta_inside(rho, 1, delta)
    assert r.assumptions_used == []


def test_explicit_delta_formula_for_nonzero_c():
    r = _cert(1, 3, function_family="polygamma")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    rho = sympy.Integer(1)
    delta = sympy.sympify(r.sufficient_delta)
    assert sympy.simplify(delta - rho / (2 * (3 + 1))) == 0
    assert delta == sympy.Rational(1, 8)
    assert _delta_inside(rho, 3, delta)


def test_half_and_two_and_negative_half_distances():
    half = _cert(sympy.Rational(1, 2), 1, function_family="polygamma")
    two = _cert(2, 1, function_family="polygamma")
    neg_half = _cert(sympy.Rational(-1, 2), 1, function_family="polygamma")
    assert half.verdict == two.verdict == neg_half.verdict == CERTIFIED_NEIGHBORHOOD
    assert sympy.sympify(half.distance_to_singularity) == sympy.Rational(1, 2)
    assert sympy.sympify(two.distance_to_singularity) == 2
    assert sympy.sympify(neg_half.distance_to_singularity) == sympy.Rational(1, 2)


def test_imaginary_z0_is_regular():
    r = _cert(sympy.I, 1, function_family="polygamma")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert sympy.sympify(r.distance_to_singularity) == 1
    r2 = _cert(1 + sympy.I, 1, function_family="polygamma")
    assert r2.verdict == CERTIFIED_NEIGHBORHOOD
    assert sympy.simplify(sympy.sympify(r2.distance_to_singularity) - sympy.sqrt(2)) == 0


def test_z0_at_pole_is_not_certified():
    for z0 in (0, -1, -2, sympy.Integer(-5)):
        r = _cert(z0, 1, function_family="polygamma")
        assert r.verdict == UNKNOWN, z0
        assert r.verdict != CERTIFIED_NEIGHBORHOOD
        assert r.distance_to_singularity == "0"


def test_constant_path_at_regular_point():
    r = _cert(1, 0, function_family="polygamma")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    blob = " ".join(r.domain_conditions).lower()
    assert "constant" in blob
    assert "z0" in blob


def test_constant_path_at_pole_is_unknown():
    r = _cert(0, 0, function_family="polygamma")
    assert r.verdict == UNKNOWN
    assert r.verdict != CERTIFIED_NEIGHBORHOOD


def test_symbolic_z0_without_exclusion_is_assumption_required():
    z0 = sympy.symbols("z0")
    r = _cert(z0, 1, function_family="polygamma")
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED_NEIGHBORHOOD
    assert r.verdict != CERTIFIED
    assert r.domain_conditions
    assert any(
        item.get("class") == C_GENERICITY for item in r.assumptions_used
    )


def test_declared_pole_exclusion_certifies_existence():
    z0 = sympy.symbols("z0")
    r = _cert(
        z0,
        1,
        assumptions=[{"class": A_DECLARED, "predicate": "z0 not in Z_<=0"}],
        function_family="polygamma",
    )
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert r.distance_to_singularity == ">0"
    assert "rho/(2*(Abs(c)+1))" in r.sufficient_delta
    assert any(item.get("class") == A_DECLARED for item in r.assumptions_used)
    assert any(item.get("class") == B_DERIVED for item in r.assumptions_used)
    assert not any(
        item.get("class") in (C_GENERICITY, D_HUMAN_REQUIRED)
        for item in r.assumptions_used
    )


def test_class_c_pole_exclusion_is_not_certified():
    z0 = sympy.symbols("z0")
    r = _cert(
        z0,
        1,
        assumptions=[{"class": C_GENERICITY, "predicate": "z0 not in Z_<=0"}],
        function_family="polygamma",
    )
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED_NEIGHBORHOOD


def test_class_d_cannot_certify_symbolic_z0():
    z0 = sympy.symbols("z0")
    r = _cert(
        z0,
        1,
        assumptions=[{"class": D_HUMAN_REQUIRED, "predicate": "beta > 0"}],
        function_family="polygamma",
    )
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED_NEIGHBORHOOD


def test_unused_class_d_does_not_block_concrete_z0():
    r = _cert(
        1,
        1,
        assumptions=[{"class": D_HUMAN_REQUIRED, "predicate": "beta > 0"}],
        function_family="polygamma",
    )
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert not any(
        item.get("class") in (C_GENERICITY, D_HUMAN_REQUIRED)
        for item in r.assumptions_used
    )


def test_declared_im_nonzero_is_class_b_for_z_le_0():
    z0 = sympy.symbols("z0")
    r = _cert(
        z0,
        1,
        assumptions=[
            {"class": A_DECLARED, "predicate": "Im(z0) != 0", "kind": "im_nonzero"}
        ],
        function_family="polygamma",
    )
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert any(item.get("class") == B_DERIVED for item in r.assumptions_used)


def test_class_c_is_ignored_when_class_a_suffices():
    z0 = sympy.symbols("z0")
    r = _cert(
        z0,
        1,
        assumptions=[
            {"class": A_DECLARED, "predicate": "z0 not in Z_<=0"},
            {"class": C_GENERICITY, "predicate": "generic parameters avoid poles"},
        ],
        function_family="polygamma",
    )
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert all(item.get("class") != C_GENERICITY for item in r.assumptions_used)


def test_unrecognized_declared_assumption_is_unknown():
    z0 = sympy.symbols("z0")
    r = _cert(
        z0,
        1,
        assumptions=[{"class": A_DECLARED, "predicate": "mu is an energy"}],
        function_family="polygamma",
    )
    assert r.verdict == UNKNOWN
    assert r.verdict != CERTIFIED_NEIGHBORHOOD


def test_re_half_plus_real_imaginary_part_has_uniform_rho():
    mu = sympy.symbols("mu", real=True)
    z0 = sympy.Rational(1, 2) + sympy.I * mu
    r = _cert(z0, 1, function_family="polygamma")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert sympy.sympify(r.distance_to_singularity) == sympy.Rational(1, 2)
    assert r.assumptions_used == []


def test_pure_imaginary_symbol_needs_exclusion():
    mu = sympy.symbols("mu", real=True)
    r = _cert(sympy.I * mu, 1, function_family="polygamma")
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED_NEIGHBORHOOD


def test_custom_pole_set_callback():
    def _cb(_z):
        return {
            "kind": "regular",
            "distance": "3",
            "isolated": True,
            "name": "custom",
        }

    z0 = sympy.symbols("z0")
    r = _cert(z0, 2, pole_set=_cb)
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert r.pole_set == "custom"
    assert sympy.sympify(r.distance_to_singularity) == 3
    delta = sympy.sympify(r.sufficient_delta)
    assert sympy.simplify(delta - sympy.Rational(3, 6)) == 0
    assert _delta_inside(3, 2, delta)


def test_pole_query_callback_and_r2_plug_in_shape():
    def r2_like(z):
        return PoleQuery(kind="pole", distance="0", isolated=True, name="r2")

    r = _cert(sympy.symbols("z0"), 1, pole_set=r2_like)
    assert r.verdict == UNKNOWN
    assert r.verdict != CERTIFIED_NEIGHBORHOOD
    assert r.pole_set == "r2"


def test_unsupported_family_is_unknown():
    r = _cert(1, 1, function_family="weierstrass_p")
    assert r.verdict == UNKNOWN
    assert r.verdict != CERTIFIED_NEIGHBORHOOD


def test_float_z0_is_unknown():
    r = _cert(0.5, 1, function_family="polygamma")
    assert r.verdict == UNKNOWN
    assert r.verdict != CERTIFIED_NEIGHBORHOOD


def test_unparsed_is_unknown():
    r = _cert("", 1, function_family="exp")
    assert r.verdict == UNKNOWN
    r2 = _cert("??not-expr??", 1, function_family="polygamma")
    assert r2.verdict == UNKNOWN


def test_symbolic_c_with_concrete_z0_still_has_explicit_delta():
    c = sympy.symbols("c")
    r = _cert(1, c, function_family="polygamma")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    delta = sympy.sympify(r.sufficient_delta)
    expect = explicit_sufficient_delta(1, c)
    assert sympy.simplify(delta - expect) == 0


def test_default_pole_set_resolver():
    assert default_pole_set("exp") is empty_pole_set
    assert default_pole_set("polygamma") is nonpositive_integer_poles
    q = empty_pole_set(sympy.symbols("z"))
    assert q.kind == "regular"
    assert q.distance == "oo"
    q2 = nonpositive_integer_poles(1)
    assert q2.kind == "regular"
    q3 = nonpositive_integer_poles(0)
    assert q3.kind == "pole"


def test_domain_conditions_always_nonempty():
    samples = [
        _cert(1, 1, function_family="exp"),
        _cert(0, 1, function_family="polygamma"),
        _cert(sympy.symbols("z0"), 1, function_family="polygamma"),
        _cert(0.5, 1, function_family="polygamma"),
        _cert(1, 1, function_family="unknown_family"),
    ]
    for r in samples:
        assert r.domain_conditions, r
        assert isinstance(r, NeighborhoodCertificate)
        assert r.assumptions_hash


def test_apply_to_remainder_does_not_mint_certified_or_zero():
    r = _cert(1, 1, function_family="exp")
    filled = r.apply_to_remainder()
    assert filled.neighborhood_verdict == CERTIFIED_NEIGHBORHOOD
    assert filled.verdict == UNKNOWN
    assert filled.verdict != CERTIFIED
    assert filled.verdict != HOP_ZERO
    assert filled.domain_conditions
    assert validate_certificate(filled) == UNKNOWN
    base = RemainderCertificate(
        function_family="exp",
        domain_conditions=["entire"],
        verdict=UNKNOWN,
    )
    filled2 = r.apply_to_remainder(base)
    assert filled2.neighborhood_verdict == CERTIFIED_NEIGHBORHOOD
    assert filled2.verdict == UNKNOWN


def test_neighborhood_does_not_compose_to_hop_zero():
    r = _cert(1, 1, function_family="exp")
    assert r.verdict != ZERO
    assert r.verdict != HOP_ZERO
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


def test_string_z0_and_c_parse():
    r = _cert("1", "1", function_family="polygamma")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert sympy.sympify(r.distance_to_singularity) == 1


def test_pi_is_regular():
    r = _cert(sympy.pi, 1, function_family="polygamma")
    assert r.verdict == CERTIFIED_NEIGHBORHOOD
    assert _delta_inside(
        sympy.sympify(r.distance_to_singularity),
        1,
        sympy.sympify(r.sufficient_delta),
    )


def test_documents_existence_theorem():
    readme = (PKG / "README.md").read_text(encoding="utf-8").lower()
    doc = (nb_mod.__doc__ or "").lower()
    blob = readme + "\n" + doc
    for tok in (
        "delta",
        "pole-free",
        "isolated",
        "c = 0",
        "existence",
        "certified_neighborhood",
        "assumption_required",
        "class c",
        "empty",
        "0,-1,-2",
    ):
        assert tok in blob, tok
    assert "hop zero" in blob or "not hop zero" in blob


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)


def test_to_dict_and_hash_stability():
    r1 = _cert(1, 1, function_family="polygamma")
    r2 = _cert(1, 1, function_family="polygamma")
    d = r1.to_dict()
    assert d["verdict"] == CERTIFIED_NEIGHBORHOOD
    assert r1.assumptions_hash == r2.assumptions_hash
    z0 = sympy.symbols("z0")
    a = [{"class": A_DECLARED, "predicate": "z0 not in Z_<=0"}]
    h1 = _cert(z0, 1, assumptions=a, function_family="polygamma").assumptions_hash
    h2 = _cert(z0, 1, assumptions=list(a), function_family="polygamma").assumptions_hash
    assert h1 == h2
