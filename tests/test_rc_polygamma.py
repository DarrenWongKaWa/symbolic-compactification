"""Polygamma pole-set predicates. No genericity insertion. Not hop ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.polygamma import (  # noqa: E402
    FALSE,
    METHOD,
    POLE_SET_EMPTY,
    POLE_SET_Z_LE_0,
    PRED_DIST_POS,
    PRED_GENERICITY,
    PRED_IDENTICALLY_POLE,
    PRED_IM_NONZERO,
    PRED_NEIGHBORHOOD,
    PRED_NOT_IDENTICALLY_POLE,
    PRED_POLE_EXCLUSION,
    TRUE,
    UNPROVED,
    classify_motivating_form,
    classify_polygamma_domain,
    motivating_affine_z0,
    order_is_entire,
    pole_set_of_order,
)
from research.remainder_certification.schema import (  # noqa: E402
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    NEIGHBORHOOD_CERTIFIED,
    NONANALYTIC,
    RemainderCertificate,
    UNKNOWN,
    remainder_cannot_be_hop_zero,
    validate_certificate,
)
from research.coefficient_laurent.schema import ZERO as HOP_ZERO_LABEL  # noqa: E402
import research.remainder_certification.polygamma as pg_pkg  # noqa: E402
import research.remainder_certification.polygamma.domain as domain_mod  # noqa: E402

PKG = ROOT / "research" / "remainder_certification" / "polygamma"
BANNED = (
    "Phi_Gamma",
    "PhiGamma",
    "phi_gamma",
    "Guo",
    "GUO",
    "G0016",
    "G0013",
    "compose_hop_verdict",
    "FAMILY_ZERO",
    "fb3b929",
)


def _pred(report, name: str):
    for item in report.predicates:
        if item.name == name:
            return item
    return None


def test_public_api():
    assert callable(classify_polygamma_domain)
    assert callable(classify_motivating_form)
    assert callable(order_is_entire)
    assert callable(pole_set_of_order)
    assert callable(motivating_affine_z0)
    assert classify_polygamma_domain is domain_mod.classify_polygamma_domain
    sig = inspect.signature(classify_polygamma_domain)
    assert list(sig.parameters)[:4] == ["k", "z0", "c", "t"]
    assert METHOD == "rc-pg-domain-1"
    assert not hasattr(pg_pkg, "compose_hop_verdict")
    assert remainder_cannot_be_hop_zero(CERTIFIED)
    assert CERTIFIED != HOP_ZERO
    assert CERTIFIED != HOP_ZERO_LABEL


def test_pole_set_split_by_order():
    assert order_is_entire(-2) is True
    assert order_is_entire(-3) is True
    assert order_is_entire(-1) is False
    assert order_is_entire(0) is False
    assert order_is_entire(2) is False
    assert order_is_entire(sympy.symbols("k")) is None
    assert pole_set_of_order(-2) == POLE_SET_EMPTY
    assert pole_set_of_order(0) == POLE_SET_Z_LE_0
    assert pole_set_of_order(-1) == POLE_SET_Z_LE_0


def test_explicit_safe_point_certified():
    t, c = sympy.symbols("t c")
    for k in (0, 1, 2, -1):
        for z0 in (
            sympy.Integer(1),
            sympy.Rational(1, 2),
            sympy.I,
            sympy.pi,
            sympy.Integer(1) + sympy.I,
        ):
            r = classify_polygamma_domain(k, z0, c, t)
            assert r.verdict == CERTIFIED, (k, z0, r.note)
            assert r.domain_usable_for_certified
            assert r.neighborhood_verdict == NEIGHBORHOOD_CERTIFIED
            assert r.domain_conditions
            assert _pred(r, PRED_NEIGHBORHOOD).status == TRUE
            fields = r.as_remainder_fields()
            assert fields["verdict"] == UNKNOWN
            assert fields["neighborhood_verdict"] == NEIGHBORHOOD_CERTIFIED
            cert = RemainderCertificate(**fields)
            assert validate_certificate(cert) == UNKNOWN
            assert cert.verdict != HOP_ZERO


def test_pole_point_nonanalytic_for_k_ge_minus_1():
    t = sympy.symbols("t")
    for k in (-1, 0, 1, 2):
        for z0 in (0, -1, -2, -5, sympy.Integer(0)):
            r = classify_polygamma_domain(k, z0, 1, t)
            assert r.verdict == NONANALYTIC, (k, z0)
            assert r.verdict != CERTIFIED
            assert _pred(r, PRED_IDENTICALLY_POLE).status == TRUE
            fields = r.as_remainder_fields()
            assert fields["verdict"] == NONANALYTIC
            cert = RemainderCertificate(**fields)
            assert validate_certificate(cert) == NONANALYTIC
            assert remainder_cannot_be_hop_zero(cert.verdict)


def test_entire_order_certified_even_at_nonpositive_integers():
    t = sympy.symbols("t")
    zoo = sympy.polygamma(-2, 0)
    assert zoo == sympy.zoo
    for k in (-2, -3, -4):
        for z0 in (0, -1, -2, 1, sympy.Rational(1, 2)):
            r = classify_polygamma_domain(k, z0, 1, t)
            assert r.verdict == CERTIFIED, (k, z0)
            assert r.entire is True
            assert r.pole_set == POLE_SET_EMPTY
            assert "entire" in r.domain_conditions
            assert r.distance_to_singularity == "oo"
            assert _pred(r, PRED_IDENTICALLY_POLE).status == FALSE


def test_sympy_polygamma_eval_not_consulted(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("domain must not evaluate sympy.polygamma as a pole oracle")

    monkeypatch.setattr(sympy, "polygamma", _boom)
    r_pole = classify_polygamma_domain(0, 0, 1, sympy.symbols("t"))
    r_safe = classify_polygamma_domain(0, 1, 1, sympy.symbols("t"))
    r_entire = classify_polygamma_domain(-2, 0, 1, sympy.symbols("t"))
    assert r_pole.verdict == NONANALYTIC
    assert r_safe.verdict == CERTIFIED
    assert r_entire.verdict == CERTIFIED


def test_symbolic_z0_without_exclusion_is_assumption_required():
    z0, t = sympy.symbols("z0 t")
    r = classify_polygamma_domain(0, z0, 1, t)
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED
    assert r.domain_usable_for_certified is False
    assert _pred(r, PRED_NOT_IDENTICALLY_POLE).status == TRUE
    assert _pred(r, PRED_DIST_POS).status == UNPROVED
    assert any(
        item.get("class") == C_GENERICITY
        and item.get("predicate") == PRED_POLE_EXCLUSION
        for item in r.missing_assumptions
    )
    assert all(
        item.get("class") not in (C_GENERICITY, D_HUMAN_REQUIRED)
        for item in r.assumptions_used
    )
    fields = r.as_remainder_fields()
    assert fields["verdict"] == ASSUMPTION_REQUIRED
    cert = RemainderCertificate(**fields)
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED


def test_real_symbol_im_zero_still_needs_exclusion():
    z0 = sympy.symbols("z0", real=True)
    r = classify_polygamma_domain(1, z0, 1, sympy.symbols("t"))
    assert r.verdict == ASSUMPTION_REQUIRED
    assert _pred(r, PRED_IM_NONZERO).status == FALSE
    assert r.verdict != CERTIFIED


def test_declared_pole_exclusion_certifies_symbolic_z0():
    z0, t = sympy.symbols("z0 t")
    r = classify_polygamma_domain(
        0,
        z0,
        1,
        t,
        declared_assumptions=[
            {"class": A_DECLARED, "predicate": "z0 not in Z_<=0"},
        ],
    )
    assert r.verdict == CERTIFIED
    assert r.domain_usable_for_certified
    assert any(
        item.get("class") == A_DECLARED
        and item.get("predicate") == PRED_POLE_EXCLUSION
        for item in r.assumptions_used
    )


def test_weak_not_identically_pole_declaration_is_not_enough():
    z0 = sympy.symbols("z0")
    r = classify_polygamma_domain(
        0,
        z0,
        declared_assumptions=[
            {"class": A_DECLARED, "predicate": "z0 not identically in Z_<=0"},
        ],
    )
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED


def test_class_c_exclusion_cannot_certify():
    z0 = sympy.symbols("z0")
    r = classify_polygamma_domain(
        0,
        z0,
        declared_assumptions=[
            {"class": C_GENERICITY, "predicate": "z0 not in Z_<=0"},
        ],
    )
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED
    assert r.domain_usable_for_certified is False


def test_positive_symbol_certified_nonnegative_not():
    t = sympy.symbols("t")
    zp = sympy.symbols("zp", positive=True)
    zn = sympy.symbols("zn", nonnegative=True)
    r_pos = classify_polygamma_domain(0, zp, 1, t)
    r_nneg = classify_polygamma_domain(0, zn, 1, t)
    assert r_pos.verdict == CERTIFIED
    assert r_nneg.verdict == ASSUMPTION_REQUIRED


def test_integer_nonpositive_symbol_nonanalytic():
    n = sympy.symbols("n", integer=True, nonpositive=True)
    r = classify_polygamma_domain(0, n, 1, sympy.symbols("t"))
    assert r.verdict == NONANALYTIC
    N = sympy.symbols("N", integer=True, positive=True)
    r_neg = classify_polygamma_domain(0, -N, 1, sympy.symbols("t"))
    assert r_neg.verdict == NONANALYTIC


def test_integer_unrestricted_symbol_assumption_required():
    n = sympy.symbols("n", integer=True)
    r = classify_polygamma_domain(0, n)
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED
    assert r.verdict != NONANALYTIC


def test_unknown_order_is_unknown():
    k, z0 = sympy.symbols("k z0")
    r = classify_polygamma_domain(k, z0)
    assert r.verdict == UNKNOWN
    assert r.verdict != CERTIFIED


def test_float_and_nonfinite_unknown():
    t = sympy.symbols("t")
    r_f = classify_polygamma_domain(0, sympy.Float("1.0"), 1, t)
    r_oo = classify_polygamma_domain(0, sympy.oo, 1, t)
    assert r_f.verdict == UNKNOWN
    assert r_oo.verdict == UNKNOWN


def test_z0_depending_on_t_unknown():
    t = sympy.symbols("t")
    r = classify_polygamma_domain(0, 1 + t, 1, t)
    assert r.verdict == UNKNOWN


def test_motivating_form_declared_reals_only_assumption_required():
    for sign in (1, -1):
        z0 = motivating_affine_z0(sign)
        assert z0 is not None
        beta, gamma, mu, epsilon = sympy.symbols(
            "beta gamma mu epsilon", real=True
        )
        assert z0.free_symbols == {beta, gamma, mu, epsilon}
        assert all(s.is_real is True for s in z0.free_symbols)
        assert all(s.is_positive is not True for s in z0.free_symbols)
        assert all(s.is_nonzero is not True for s in z0.free_symbols)
        r = classify_motivating_form(sign, k=0, c=1)
        assert r.verdict == ASSUMPTION_REQUIRED, (sign, r.verdict, r.note)
        assert r.verdict != CERTIFIED
        assert r.domain_usable_for_certified is False
        assert _pred(r, PRED_NOT_IDENTICALLY_POLE).status == TRUE
        assert _pred(r, PRED_IDENTICALLY_POLE).status == FALSE
        assert _pred(r, PRED_IM_NONZERO).status == UNPROVED
        assert _pred(r, PRED_DIST_POS).status == UNPROVED
        assert any(
            item.get("class") == C_GENERICITY
            and item.get("predicate") == PRED_POLE_EXCLUSION
            for item in r.missing_assumptions
        )
        im = sympy.simplify(sympy.im(z0))
        assert im.free_symbols
        assert sympy.expand(im) != 0
        fields = r.as_remainder_fields()
        assert fields["verdict"] == ASSUMPTION_REQUIRED
        cert = RemainderCertificate(**fields)
        assert validate_certificate(cert) == ASSUMPTION_REQUIRED
        assert cert.verdict != HOP_ZERO
        assert remainder_cannot_be_hop_zero(cert.verdict)


def test_motivating_form_beta_positive_still_not_certified():
    r_a = classify_motivating_form(
        1,
        declared_assumptions=[
            {"class": A_DECLARED, "predicate": "beta > 0"},
        ],
    )
    r_d = classify_motivating_form(
        1,
        declared_assumptions=[
            {"class": D_HUMAN_REQUIRED, "predicate": "beta > 0"},
        ],
    )
    assert r_a.verdict == ASSUMPTION_REQUIRED
    assert r_d.verdict == ASSUMPTION_REQUIRED
    assert r_a.verdict != CERTIFIED
    assert r_d.verdict != CERTIFIED


def test_motivating_form_declared_im_or_exclusion_certified():
    r_im = classify_motivating_form(
        1,
        declared_assumptions=[
            {"class": A_DECLARED, "predicate": "Im(z0) identically nonzero"},
        ],
    )
    r_ex = classify_motivating_form(
        -1,
        declared_assumptions=[
            {"class": A_DECLARED, "predicate": "z0 not in Z_<=0"},
        ],
    )
    assert r_im.verdict == CERTIFIED
    assert r_ex.verdict == CERTIFIED
    assert r_im.domain_usable_for_certified
    assert r_ex.domain_usable_for_certified
    assert all(
        item.get("class") not in (C_GENERICITY, D_HUMAN_REQUIRED)
        for item in r_im.assumptions_used + r_ex.assumptions_used
    )


def test_genericity_slogan_not_treated_as_exclusion():
    z0 = sympy.symbols("z0")
    r = classify_polygamma_domain(
        0,
        z0,
        declared_assumptions=[
            {"class": A_DECLARED, "predicate": "generic parameters avoid poles"},
        ],
    )
    assert r.verdict == ASSUMPTION_REQUIRED
    assert r.verdict != CERTIFIED
    assert PRED_GENERICITY in {
        domain_mod._canonicalize_predicate_text("generic parameters avoid poles")
    }


def test_constant_c_zero_still_certified_off_pole():
    t = sympy.symbols("t")
    r = classify_polygamma_domain(0, 1, 0, t)
    assert r.verdict == CERTIFIED
    assert "path constant" in r.required_small_t_condition


def test_domain_conditions_never_empty():
    cases = [
        classify_polygamma_domain(0, 1),
        classify_polygamma_domain(0, 0),
        classify_polygamma_domain(0, sympy.symbols("z0")),
        classify_polygamma_domain(-2, 0),
        classify_polygamma_domain(sympy.symbols("k"), 1),
        classify_motivating_form(1),
    ]
    for r in cases:
        assert r.domain_conditions, r
        cert = RemainderCertificate(**r.as_remainder_fields())
        assert cert.domain_conditions
        assert validate_certificate(cert) != CERTIFIED or r.verdict != CERTIFIED
        assert remainder_cannot_be_hop_zero(validate_certificate(cert))


def test_remainder_fields_do_not_mint_certified_remainder():
    r = classify_polygamma_domain(0, 1, 1, sympy.symbols("t"))
    assert r.verdict == CERTIFIED
    fields = r.as_remainder_fields()
    assert fields["verdict"] != CERTIFIED
    assert fields["verdict"] == UNKNOWN
    assert fields["analyticity_certificate"]["domain_verdict"] == CERTIFIED
    cert = RemainderCertificate(**fields, remainder_form="unset")
    assert validate_certificate(cert) == UNKNOWN
    assert cert.verdict != HOP_ZERO_LABEL


def test_source_ban_and_docs():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
        assert "compose_hop_verdict" not in src
        assert "sympy.limit" not in src
        assert ".limit(" not in src
    py = Path(domain_mod.__file__).read_text(encoding="utf-8")
    assert "DLMF 5.15.1" in py
    assert "Espinosa" in py
    assert "class C/D is never inserted" in py or "Class C/D is never inserted" in py
    assert "not identically" in py.lower()
    assert "zoo" in py
    readme = (PKG / "README.md").read_text(encoding="utf-8")
    assert "ASSUMPTION_REQUIRED" in readme
    assert "not CERTIFIED" in readme
    assert "DLMF" in readme
    assert "real=True" in readme
    init_src = (PKG / "__init__.py").read_text(encoding="utf-8")
    assert "not remainder CERTIFIED" in init_src
