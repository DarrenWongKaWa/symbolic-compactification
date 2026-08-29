"""Hidden remainder hypotheses cannot CERTIFY and cannot promote hop ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.assumption_audit import (  # noqa: E402
    RULE_IDS,
    AssumptionLeak,
    apply_assumption_gate,
    audit_certificate,
    blocks_certified,
    blocks_hop_zero_promotion,
    certificate_silent_leaks,
    engine_path,
    has_hidden_hypotheses,
    iter_remainder_python,
    scan_all,
    scan_engine,
    scan_remainder_python,
    scan_text,
)
from research.remainder_certification.schema import (  # noqa: E402
    A_DECLARED,
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
    LEVEL_C,
    ZERO,
    compose_hop_verdict,
)
from research.coefficient_laurent.schema import UNKNOWN as HOP_UNKNOWN  # noqa: E402

RC = ROOT / "research" / "remainder_certification"
POLICY = RC / "ASSUMPTION_POLICY.md"
ENGINE = ROOT / "research" / "coefficient_laurent" / "engine.py"

BANNED_EXACT = (
    "beta > 0",
    "assume generic",
    "energy arguments",
)

MISSION_RULES = {
    "positive_beta",
    "nonzero_gamma",
    "real_mu_kw",
    "energy_diff_nonzero",
    "not_polygamma_pole",
    "generic_parameters",
    "half_plus_ie",
    "assume_generic",
    "energy_arguments",
}

# Attack snippets live here, not in remainder_certification production Python.
ATTACKS = (
    ("positive_beta", "hypotheses.setdefault('beta', 'beta > 0')"),
    ("assume_generic", "# assume generic"),
    ("energy_arguments", "# frozen kernels (energy arguments ~ 1/2 + i E)"),
    ("half_plus_ie", "remainder_verdict = ZERO  # 1/2 + iE never hits poles"),
    ("generic_parameters", "# generic parameters avoid poles"),
    ("nonzero_gamma", "assert gamma != 0"),
    ("real_mu_kw", "mu = sympy.symbols('mu', real=True)"),
    ("energy_diff_nonzero", "# energy differences nonzero"),
    ("not_polygamma_pole", "# argument not at polygamma pole"),
    ("cauchy_m_finite", "bound = M < oo"),
    ("sufficiently_small_t", "# sufficiently small t"),
    ("real_only_path", "# real-only path"),
)

RETRACTED_ENGINE_COMMENT = (
    "# for the frozen Guo kernels (energy arguments ~ 1/2 + i E). Remainder"
)

SIBLINGS = (
    "analysis",
    "polygamma",
    "neighborhood",
    "cauchy",
    "order_algebra",
    "derivatives",
    "affine",
    "compiler",
    "falsifier",
    "numeric",
    "literature",
    "alternatives",
)


def _compose_all_zero(remainder_verdict: str) -> tuple[str, str]:
    return compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=remainder_verdict,
    )


def test_public_api():
    assert callable(scan_text)
    assert callable(scan_remainder_python)
    assert callable(scan_engine)
    assert callable(scan_all)
    assert callable(audit_certificate)
    assert callable(apply_assumption_gate)
    assert callable(blocks_certified)
    assert callable(blocks_hop_zero_promotion)
    sig = inspect.signature(apply_assumption_gate)
    assert "leaks" in sig.parameters
    assert MISSION_RULES <= RULE_IDS
    assert "cauchy_m_finite" in RULE_IDS
    assert "sufficiently_small_t" in RULE_IDS
    assert "real_only_path" in RULE_IDS


def test_required_anchors_exist():
    assert (RC / "schema.py").is_file()
    assert POLICY.is_file()
    leaks = scan_remainder_python(ROOT)
    assert isinstance(leaks, list)
    names = {p.name for p in iter_remainder_python(ROOT)}
    assert "schema.py" in names
    assert "scan.py" in names


def test_sibling_packages_may_be_absent():
    for name in SIBLINGS:
        _ = (RC / name).exists()
    leaks = scan_all(ROOT)
    assert leaks == []


def test_live_remainder_python_has_no_silent_leaks():
    assert scan_remainder_python(ROOT) == []
    assert scan_all(ROOT) == []


def test_remainder_python_omits_banned_silent_tokens():
    for path in iter_remainder_python(ROOT):
        src = path.read_text(encoding="utf-8")
        for tok in BANNED_EXACT:
            assert tok not in src, f"{path} contains {tok!r}"


def test_live_engine_has_no_retracted_shortcut():
    leaks = scan_engine(ROOT)
    assert leaks == []
    path = engine_path(ROOT)
    if path.is_file():
        src = path.read_text(encoding="utf-8")
        assert "energy arguments" not in src
        assert "1/2 + i E" not in src
        assert "remainder_ok" in src


def test_missing_engine_is_clean():
    leaks = scan_engine(ROOT, path=RC / "no_such_engine.py")
    assert leaks == []


def test_clean_source_is_not_a_leak():
    src = "domain_conditions = ['entire']\nverdict = CERTIFIED\n"
    assert scan_text(src) == []
    assert not has_hidden_hypotheses(leaks=scan_text(src))


@pytest.mark.parametrize("rule_id,snippet", ATTACKS, ids=[rule_id for rule_id, _snippet in ATTACKS])
def test_attack_snippet_is_detected(rule_id, snippet):
    leaks = scan_text(snippet)
    assert leaks
    assert rule_id in {item.rule_id for item in leaks}
    assert has_hidden_hypotheses(leaks=leaks)
    assert blocks_certified(leaks)
    assert blocks_hop_zero_promotion(leaks)
    assert apply_assumption_gate(CERTIFIED, leaks=leaks) == ASSUMPTION_REQUIRED
    assert apply_assumption_gate(HOP_ZERO, leaks=leaks) == UNKNOWN
    assert apply_assumption_gate(UNKNOWN, leaks=leaks) == UNKNOWN


def test_retracted_engine_comment_cannot_certify_or_zero():
    leaks = scan_text(RETRACTED_ENGINE_COMMENT)
    assert leaks
    assert {"energy_arguments", "half_plus_ie"} <= {item.rule_id for item in leaks}
    assert apply_assumption_gate(CERTIFIED, leaks=leaks) == ASSUMPTION_REQUIRED
    rem = apply_assumption_gate(ZERO, leaks=leaks)
    assert rem != ZERO
    v, lvl = _compose_all_zero(rem)
    assert v == HOP_UNKNOWN
    assert v != ZERO
    assert lvl == LEVEL_B
    assert (v, lvl) != (ZERO, LEVEL_C)


def test_engine_scan_flags_retracted_comment(tmp_path):
    path = tmp_path / "engine.py"
    path.write_text(RETRACTED_ENGINE_COMMENT + "\n", encoding="utf-8")
    leaks = scan_engine(ROOT, path=path)
    assert leaks
    assert {item.rule_id for item in leaks} & {"energy_arguments", "half_plus_ie"}


def test_declared_class_a_may_be_certified():
    cert = RemainderCertificate(
        function_family="exp",
        domain_conditions=["entire"],
        assumptions_used=[{"class": A_DECLARED, "predicate": "f is entire"}],
        verdict=CERTIFIED,
    )
    assert validate_certificate(cert) == CERTIFIED
    assert audit_certificate(cert) == CERTIFIED
    assert certificate_silent_leaks(cert) == []
    assert not has_hidden_hypotheses(cert=cert)
    assert not blocks_certified(cert=cert)
    assert remainder_cannot_be_hop_zero(cert.verdict)
    assert CERTIFIED != HOP_ZERO
    assert CERTIFIED != ZERO


def test_declared_class_a_predicate_is_not_silent():
    cert = RemainderCertificate(
        domain_conditions=["beta > 0"],
        assumptions_used=[{"class": A_DECLARED, "predicate": "beta > 0"}],
        verdict=CERTIFIED,
    )
    assert certificate_silent_leaks(cert) == []
    assert audit_certificate(cert) == CERTIFIED
    assert not has_hidden_hypotheses(cert=cert)


def test_undeclared_domain_predicate_cannot_certified():
    cert = RemainderCertificate(
        domain_conditions=["beta > 0"],
        verdict=CERTIFIED,
    )
    assert certificate_silent_leaks(cert)
    assert audit_certificate(cert) == ASSUMPTION_REQUIRED
    assert blocks_certified(cert=cert)
    assert blocks_hop_zero_promotion(cert=cert)
    rem = apply_assumption_gate(ZERO, cert=cert)
    v, lvl = _compose_all_zero(rem)
    assert v != ZERO
    assert lvl != LEVEL_C or v != ZERO


def test_unlabeled_assumption_predicate_is_silent():
    cert = RemainderCertificate(
        domain_conditions=["entire"],
        assumptions_used=[{"predicate": "assume generic"}],
        verdict=CERTIFIED,
    )
    assert certificate_silent_leaks(cert)
    assert audit_certificate(cert) == ASSUMPTION_REQUIRED


def test_hidden_analyticity_note_cannot_certified():
    cert = RemainderCertificate(
        domain_conditions=["entire"],
        analyticity_certificate={"why": "generic parameters"},
        verdict=CERTIFIED,
    )
    assert audit_certificate(cert) == ASSUMPTION_REQUIRED
    assert apply_assumption_gate(CERTIFIED, cert=cert) == ASSUMPTION_REQUIRED


def test_class_c_cannot_be_certified():
    cert = RemainderCertificate(
        domain_conditions=["alpha_0 not a pole (genericity)"],
        assumptions_used=[{"class": C_GENERICITY, "predicate": "alpha_0 not in Z_<=0"}],
        verdict=CERTIFIED,
    )
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED
    assert audit_certificate(cert) == ASSUMPTION_REQUIRED
    assert has_hidden_hypotheses(cert=cert)


def test_class_d_cannot_be_certified():
    cert = RemainderCertificate(
        domain_conditions=["human physics bound"],
        assumptions_used=[{"class": D_HUMAN_REQUIRED, "predicate": "beta > 0"}],
        verdict=CERTIFIED,
    )
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED
    assert audit_certificate(cert) == ASSUMPTION_REQUIRED
    assert blocks_hop_zero_promotion(cert=cert)


def test_audit_does_not_upgrade():
    empty = RemainderCertificate(verdict=CERTIFIED, domain_conditions=[])
    assert audit_certificate(empty) == UNKNOWN
    unknown = RemainderCertificate(domain_conditions=["entire"], verdict=UNKNOWN)
    assert audit_certificate(unknown) == UNKNOWN
    nonanalytic = RemainderCertificate(domain_conditions=["pole"], verdict=NONANALYTIC)
    assert audit_certificate(nonanalytic) == NONANALYTIC


def test_attack_certificates_are_not_certified():
    for rule_id, snippet in ATTACKS:
        cert = RemainderCertificate(domain_conditions=[snippet], verdict=CERTIFIED)
        assert audit_certificate(cert) == ASSUMPTION_REQUIRED, rule_id
        assert remainder_cannot_be_hop_zero(audit_certificate(cert))


def test_hidden_hypothesis_cannot_promote_hop_zero():
    leaks = scan_text("# assume generic")
    rem = apply_assumption_gate(ZERO, leaks=leaks)
    assert rem == HOP_UNKNOWN
    v, lvl = _compose_all_zero(rem)
    assert v == HOP_UNKNOWN
    assert v != ZERO
    assert lvl == LEVEL_B
    assert lvl != LEVEL_C or v != ZERO


def test_forbidden_ignore_remainder_regression():
    v, lvl = _compose_all_zero(HOP_UNKNOWN)
    assert v == HOP_UNKNOWN
    assert v != ZERO
    assert lvl == LEVEL_B


def test_does_not_revive_retracted_level_c_zero():
    leaks = scan_text(RETRACTED_ENGINE_COMMENT)
    rem = apply_assumption_gate(ZERO, leaks=leaks)
    v, lvl = _compose_all_zero(rem)
    assert (v, lvl) != (ZERO, LEVEL_C)
    cert = RemainderCertificate(
        domain_conditions=["energy arguments ~ 1/2 + i E"],
        verdict=CERTIFIED,
    )
    assert audit_certificate(cert) != CERTIFIED
    assert apply_assumption_gate(CERTIFIED, cert=cert) != CERTIFIED


def test_policy_lists_r10_forbidden_insertions():
    text = POLICY.read_text(encoding="utf-8")
    assert "Subagent R10 must test these" in text
    lower = text.lower()
    assert "positive" in lower and "beta" in lower
    assert "nonzero" in lower and "gamma" in lower
    assert "energy differences nonzero" in lower
    assert "polygamma pole" in lower
    assert "generic" in lower


def test_assumption_leak_is_serializable():
    leaks = scan_text("# assume generic")
    assert leaks
    blob = leaks[0].to_dict()
    assert blob["rule_id"] == "assume_generic"
    assert blob["klass"] == C_GENERICITY
    assert isinstance(leaks[0], AssumptionLeak)


def test_main_exits_clean_on_live_tree():
    from research.remainder_certification.assumption_audit.scan import main

    assert main([str(ROOT)]) == 0
