"""Alternative remainder backends. Not CASE R-E. Never hop ZERO."""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.alternatives import (  # noqa: E402
    CASE_R_E,
    CONTINUE_CUSTOM,
    RECOMMENDATION,
    run_probe,
)
from research.remainder_certification.alternatives import probe as probe_mod  # noqa: E402
from research.remainder_certification.schema import (  # noqa: E402
    CERTIFIED,
    RemainderCertificate,
    remainder_cannot_be_hop_zero,
    validate_certificate,
)
from research.coefficient_laurent.remainder import (  # noqa: E402
    remainder_ok,
    remainder_verdict,
)
from research.coefficient_laurent.schema import (  # noqa: E402
    LEVEL_B,
    ZERO,
    compose_hop_verdict,
)
from research.coefficient_laurent.schema import UNKNOWN as HOP_UNKNOWN  # noqa: E402

PKG = ROOT / "research" / "remainder_certification" / "alternatives"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "PhiGamma")


def test_public_api():
    assert RECOMMENDATION == CONTINUE_CUSTOM
    assert RECOMMENDATION != CASE_R_E
    assert CASE_R_E == "CASE_R_E"
    assert callable(run_probe)
    assert inspect.signature(run_probe).parameters == {}
    assert probe_mod.RECOMMENDATION == CONTINUE_CUSTOM


def test_recommendation_rejects_case_r_e():
    rec = run_probe()
    assert rec["recommendation"] == CONTINUE_CUSTOM
    assert rec["case_r_e_accepted"] is False
    assert rec["case_r_e"] is None
    assert rec["d2"] == "LOCKED"
    assert rec["decision"]["case_r_e_accepted"] is False
    assert "ZERO" not in rec["recommendation"]
    assert "CERTIFIED" not in rec["recommendation"]
    assert rec["note"]
    assert "hop ZERO" in rec["note"]
    assert rec["case_r_e"] is None
    assert json.dumps(rec, default=str)


def test_v5_remainder_ok_symbolic_alpha_unknown():
    t, a = sympy.symbols("t a")
    assert remainder_ok(1 + t, t) is True
    assert remainder_ok(a + t, t) is False
    assert remainder_verdict(a + t, t) == HOP_UNKNOWN
    assert remainder_verdict(a + t, t) != ZERO
    v5 = probe_mod.probe_v5_remainder_ok()
    assert v5["symbolic_alpha_insufficient"] is True
    assert v5["never_hop_zero_on_symbolic"] is True


def test_holonomic_cannot_convert_polygamma():
    hol = probe_mod.probe_holonomic()
    assert hol["d_finite_table_has_exp_sin"] is True
    assert hol["polygamma_converted"] is False
    assert hol["gamma_converted"] is False


def test_flint_arb_absent_and_iv_has_no_psi():
    ball = probe_mod.probe_ball_arithmetic()
    assert ball["flint_importable"] is False
    assert ball["arb_importable"] is False
    assert ball["python_flint"]["available"] is False
    assert ball["symbolic_alpha_possible"] is False
    assert ball["iv_psi_ok"] is False
    assert ball["iv_attr"].get("psi") is not True
    assert ball["iv_attr"].get("polygamma") is not True


def test_sympy_series_order_is_not_a_bound():
    series = probe_mod.probe_sympy_series()
    assert series["symbolic_emits_order_marker"] is True
    assert series["pole_raises"] is True
    assert series["order_is_truncation_marker_not_bound"] is True
    assert "zoo" in (series["subs_symbolic_series_at_pole"] or "")


def test_identities_do_not_discharge_symbolic_alpha():
    ids = probe_mod.probe_identities()
    assert ids["recurrence_n0"] is True
    assert ids["recurrence_n1"] is True
    assert ids["identities_discharge_symbolic_alpha"] is False
    assert ids["remainder_ok_still_unknown"] is True


def test_singularities_miss_polygamma_poles():
    sing = probe_mod.probe_singularities()
    assert sing["polygamma_poles_empty"] is True
    assert sing["cannot_certify_domain"] is True


def test_probe_never_mints_hop_zero_or_remainder_certified():
    rec = run_probe()
    assert rec["recommendation"] != ZERO
    assert rec["recommendation"] != CERTIFIED
    assert rec["case_r_e_accepted"] is False
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


def test_remainder_certified_is_still_not_hop_zero():
    cert = RemainderCertificate(
        function_family="exp",
        domain_conditions=["entire"],
        verdict=CERTIFIED,
    )
    assert validate_certificate(cert) == CERTIFIED
    assert remainder_cannot_be_hop_zero(cert.verdict)
    assert cert.verdict != ZERO


def test_matrix_documents_decision():
    matrix = (PKG / "MATRIX.md").read_text(encoding="utf-8")
    readme = (PKG / "README.md").read_text(encoding="utf-8")
    blob = matrix + "\n" + readme
    for tok in (
        "CASE R-E",
        "CONTINUE_CUSTOM",
        "Soundness",
        "Decidability",
        "Dependency",
        "Use now",
        "LOCKED",
        "remainder_ok",
        "holonomic",
        "python-flint",
        "ASSUMPTION_REQUIRED",
    ):
        assert tok in blob, tok
    assert "not **CASE R-E**" in matrix or "not CASE R-E" in matrix
    assert "Do not pip" in readme or "Do not `pip install`" in readme


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
