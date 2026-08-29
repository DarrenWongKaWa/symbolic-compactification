"""Atom-local RemainderCertificate compiler. CERTIFIED is not hop ZERO."""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.schema import (  # noqa: E402
    LEVEL_B,
    ZERO,
    compose_hop_verdict,
)
from research.remainder_certification.compiler import (  # noqa: E402
    SIBLING_PACKAGES,
    compile_remainder,
    resolve_step,
    sibling_status,
)
from research.remainder_certification.compiler.builders import (  # noqa: E402
    EMPTY_DOMAIN_CONDITION,
    hash_assumptions,
    remainder_form_for_order,
    sha256_text,
)
from research.remainder_certification.schema import (  # noqa: E402
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    METHOD_VERSION,
    NEIGHBORHOOD_CERTIFIED,
    NONANALYTIC,
    RemainderCertificate,
    UNKNOWN,
    remainder_cannot_be_hop_zero,
    validate_certificate,
)
import research.remainder_certification.compiler as compiler_pkg   # noqa: E402
import research.remainder_certification.compiler.compile as compile_mod   # noqa: E402

PKG = ROOT / "research" / "remainder_certification" / "compiler"
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
    "sparse_laurent_limit",
)


def _affine_ok(payload):
    return {
        "ok": True,
        "expansion_point": "1",
        "perturbation": "1",
        "argument": "1 + t",
    }


def _neighborhood_ok(payload):
    return {
        "verdict": NEIGHBORHOOD_CERTIFIED,
        "domain_conditions": ["disk |z-1|<1 is pole-free"],
        "distance_to_singularity": "1",
        "required_small_t_condition": "exists delta>0: |t|<delta => |c t|<1/2",
    }


def _cauchy_ok(payload):
    n = payload.get("taylor_order")
    form = remainder_form_for_order(n) if isinstance(n, int) else "R_{N+1}(t)"
    return {
        "ok": True,
        "remainder_form": form,
        "bound": "M |c t|^{N+1} / (r^N (r - |c t|))",
        "proof_dependencies": ["Cauchy integral remainder"],
    }


def _analysis_ok(payload):
    return {
        "verdict": CERTIFIED,
        "domain_conditions": ["entire"],
        "analyticity_certificate": {"kind": "entire"},
        "distance_to_singularity": "inf",
        "assumptions_used": [
            {"class": A_DECLARED, "predicate": "exp entire on C"}
        ],
        "proof_dependencies": ["entire Taylor theorem"],
    }


def _certified_kwargs(**overrides):
    kw = {
        "affine": _affine_ok,
        "neighborhood": _neighborhood_ok,
        "cauchy": _cauchy_ok,
        "analysis": _analysis_ok,
    }
    kw.update(overrides)
    return kw


def _full(atom="exp", affine_argument="1 + t", domain=None, order=3, **overrides):
    if domain is None:
        domain = {
            "verdict": CERTIFIED,
            "domain_conditions": ["entire"],
            "analyticity_certificate": {"kind": "entire"},
        }
    return compile_remainder(
        atom,
        affine_argument,
        domain,
        order,
        **_certified_kwargs(**overrides),
    )


def test_public_api():
    assert callable(compile_remainder)
    assert compile_remainder is compile_mod.compile_remainder
    assert compiler_pkg.compile_remainder is compile_remainder
    sig = inspect.signature(compile_remainder)
    params = list(sig.parameters)
    assert params[:4] == [
        "atom",
        "affine_argument",
        "domain_certificate",
        "taylor_order",
    ]
    for name in ("affine", "neighborhood", "cauchy", "polygamma", "analysis"):
        assert name in sig.parameters
        assert sig.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
    assert SIBLING_PACKAGES["affine"].endswith(".affine")
    assert not hasattr(compiler_pkg, "compose_hop_verdict")
    assert METHOD_VERSION == "rc-remainder-cert-1"


def test_missing_siblings_unknown_not_certified():
    disabled = False
    for name in ("affine", "neighborhood", "cauchy", "polygamma", "analysis"):
        fn, src = resolve_step(name, disabled)
        assert fn is None
        assert src == "injected_not_callable"
    cert = compile_remainder(
        "exp",
        {"expansion_point": "0", "perturbation": "1", "argument": "t"},
        {
            "verdict": CERTIFIED,
            "domain_conditions": ["entire"],
            "analyticity_certificate": {"kind": "entire"},
        },
        2,
        affine=disabled,
        neighborhood=disabled,
        cauchy=disabled,
        polygamma=disabled,
        analysis=disabled,
    )
    assert cert.verdict == UNKNOWN
    assert validate_certificate(cert) == UNKNOWN
    assert cert.verdict != CERTIFIED
    assert cert.verdict != HOP_ZERO
    assert cert.domain_conditions
    assert "entire" in cert.domain_conditions
    assert "missing" in cert.note or "injected_not_callable" in cert.note
    assert cert.method_version == METHOD_VERSION


def test_every_certificate_has_domain_conditions():
    cert = compile_remainder("log")
    assert cert.domain_conditions
    assert validate_certificate(cert) != CERTIFIED
    assert cert.verdict == UNKNOWN
    assert EMPTY_DOMAIN_CONDITION in cert.domain_conditions or any(
        cert.domain_conditions
    )


def test_injected_steps_can_certify():
    cert = _full()
    assert validate_certificate(cert) == CERTIFIED
    assert cert.verdict == CERTIFIED
    assert cert.function_family == "exp"
    assert cert.expansion_order == 3
    assert cert.expansion_point == "1"
    assert cert.perturbation == "1"
    assert cert.argument == "1 + t"
    assert cert.neighborhood_verdict == NEIGHBORHOOD_CERTIFIED
    assert cert.bound
    assert cert.remainder_form == remainder_form_for_order(3)
    assert cert.required_small_t_condition
    assert cert.analyticity_certificate.get("kind") == "entire"
    assert cert.domain_conditions
    assert cert.assumptions_hash == hash_assumptions(cert.assumptions_used)
    assert cert.argument_text_hash == sha256_text(cert.argument)
    assert cert.method_version == METHOD_VERSION
    assert remainder_cannot_be_hop_zero(cert.verdict)


def test_certified_remainder_is_not_hop_zero():
    cert = _full()
    assert cert.verdict == CERTIFIED
    assert cert.verdict != HOP_ZERO
    assert CERTIFIED != ZERO
    assert CERTIFIED != HOP_ZERO
    assert remainder_cannot_be_hop_zero(CERTIFIED)
    assert cert.neighborhood_verdict != HOP_ZERO


def test_certified_remainder_does_not_compose_hop_zero():
    cert = _full()
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=cert.verdict,
    )
    assert cert.verdict == CERTIFIED
    assert v == UNKNOWN
    assert v != ZERO
    assert lvl == LEVEL_B


def test_class_c_cannot_be_certified():
    cert = _full(
        declared_assumptions=[
            {"class": C_GENERICITY, "predicate": "alpha_0 not in Z_<=0"}
        ]
    )
    assert cert.verdict == ASSUMPTION_REQUIRED
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED
    assert cert.verdict != CERTIFIED
    assert cert.domain_conditions


def test_class_d_cannot_be_certified():
    cert = _full(
        declared_assumptions=[
            {"class": D_HUMAN_REQUIRED, "predicate": "beta > 0"}
        ]
    )
    assert cert.verdict == ASSUMPTION_REQUIRED
    assert validate_certificate(cert) == ASSUMPTION_REQUIRED
    assert cert.verdict != CERTIFIED


def test_unclassified_assumption_cannot_be_certified():
    cert = _full(declared_assumptions=[{"predicate": "generic parameters"}])
    assert cert.verdict != CERTIFIED
    assert cert.verdict == ASSUMPTION_REQUIRED
    assert validate_certificate(cert) != CERTIFIED


def test_empty_domain_not_certified_even_with_fakes():
    def neigh_empty(payload):
        return {"verdict": NEIGHBORHOOD_CERTIFIED}

    cert = compile_remainder(
        "exp",
        {"expansion_point": "0", "perturbation": "1", "argument": "t"},
        {"verdict": CERTIFIED, "domain_conditions": []},
        1,
        affine=_affine_ok,
        neighborhood=neigh_empty,
        cauchy=_cauchy_ok,
    )
    assert cert.domain_conditions
    assert cert.verdict != CERTIFIED
    assert validate_certificate(cert) != CERTIFIED
    assert validate_certificate(
        RemainderCertificate(verdict=CERTIFIED, domain_conditions=[])
    ) == UNKNOWN


def test_nonanalytic_domain_not_certified():
    cert = _full(
        domain={
            "verdict": NONANALYTIC,
            "domain_conditions": ["z0 is a pole"],
        },
        analysis=lambda payload: {
            "verdict": NONANALYTIC,
            "domain_conditions": ["z0 is a pole"],
        },
    )
    assert cert.verdict == NONANALYTIC
    assert validate_certificate(cert) == NONANALYTIC
    assert cert.verdict != CERTIFIED
    assert cert.verdict != HOP_ZERO


def test_analysis_nonanalytic_overrides_certified_input():
    cert = _full(
        analysis=lambda payload: {
            "verdict": NONANALYTIC,
            "domain_conditions": ["path hits a pole"],
        }
    )
    assert cert.verdict == NONANALYTIC


def test_invalid_taylor_order_unknown():
    for order in (None, -1, True, "3", 1.5):
        cert = _full(order=order)
        assert cert.verdict == UNKNOWN
        assert cert.verdict != CERTIFIED
        assert cert.domain_conditions


def test_unstructured_affine_without_normalizer_unknown():
    cert = compile_remainder(
        "exp",
        "1 + t",
        {"verdict": CERTIFIED, "domain_conditions": ["entire"]},
        2,
        neighborhood=_neighborhood_ok,
        cauchy=_cauchy_ok,
        analysis=_analysis_ok,
    )
    assert cert.verdict == UNKNOWN
    assert cert.argument == "1 + t"
    assert cert.domain_conditions


def test_structured_affine_without_affine_package_can_certify():
    cert = compile_remainder(
        "exp",
        {"expansion_point": "1", "perturbation": "1", "argument": "1 + t"},
        {"verdict": CERTIFIED, "domain_conditions": ["entire"]},
        2,
        affine=False,
        neighborhood=_neighborhood_ok,
        cauchy=_cauchy_ok,
        analysis=_analysis_ok,
    )
    assert cert.verdict == CERTIFIED
    assert cert.expansion_point == "1"


def test_certified_without_analysis_or_affine_callables():
    """Primary inputs plus neighborhood/Cauchy steps; no sibling packages."""
    cert = compile_remainder(
        {"function_family": "exp", "function_order": ""},
        {"expansion_point": "0", "perturbation": "1", "argument": "t"},
        {
            "verdict": CERTIFIED,
            "domain_conditions": ["entire"],
            "analyticity_certificate": {"kind": "entire"},
            "assumptions_used": [
                {"class": A_DECLARED, "predicate": "declared entire"}
            ],
        },
        0,
        affine=False,
        neighborhood=_neighborhood_ok,
        cauchy=_cauchy_ok,
        polygamma=False,
        analysis=False,
    )
    assert cert.verdict == CERTIFIED
    assert validate_certificate(cert) == CERTIFIED
    assert cert.expansion_order == 0
    assert cert.remainder_form == remainder_form_for_order(0)
    assert cert.verdict != HOP_ZERO
    assert "entire" in cert.domain_conditions


def test_neighborhood_assumption_required():
    cert = _full(
        neighborhood=lambda payload: {
            "verdict": ASSUMPTION_REQUIRED,
            "domain_conditions": ["need pole exclusion"],
        }
    )
    assert cert.verdict == ASSUMPTION_REQUIRED
    assert cert.neighborhood_verdict == ASSUMPTION_REQUIRED
    assert cert.verdict != CERTIFIED


def test_neighborhood_remainder_certified_is_not_neighborhood_certified():
    cert = _full(neighborhood=lambda payload: {"verdict": CERTIFIED})
    assert cert.neighborhood_verdict != NEIGHBORHOOD_CERTIFIED
    assert cert.verdict != CERTIFIED


def test_cauchy_missing_blocks_certified():
    cert = compile_remainder(
        "exp",
        {"expansion_point": "0", "perturbation": "1", "argument": "t"},
        {"verdict": CERTIFIED, "domain_conditions": ["entire"]},
        2,
        affine=_affine_ok,
        neighborhood=_neighborhood_ok,
        analysis=_analysis_ok,
    )
    assert cert.verdict == UNKNOWN
    assert cert.verdict != CERTIFIED
    assert "cauchy" in cert.note


def test_raising_callable_fail_closed():
    def boom(payload):
        raise RuntimeError("nope")

    cert = _full(cauchy=boom)
    assert cert.verdict == UNKNOWN
    assert cert.verdict != CERTIFIED
    assert cert.domain_conditions


def test_polygamma_unknown_does_not_block_non_pg_family():
    cert = _full(polygamma=lambda payload: {"verdict": UNKNOWN})
    assert cert.verdict == CERTIFIED


def test_polygamma_nonanalytic_counts_for_any_family():
    cert = _full(
        polygamma=lambda payload: {
            "verdict": NONANALYTIC,
            "domain_conditions": ["argument is a pole"],
        }
    )
    assert cert.verdict == NONANALYTIC


def test_hashes_are_sha256_of_canonical_payload():
    cert = _full()
    assert cert.argument_text_hash == hashlib.sha256(
        cert.argument.encode("utf-8")
    ).hexdigest()
    blob = json.dumps(
        cert.assumptions_used, sort_keys=True, default=str, separators=(",", ":")
    )
    assert cert.assumptions_hash == hashlib.sha256(blob.encode("utf-8")).hexdigest()


def test_to_dict_roundtrip_fields():
    cert = _full()
    data = cert.to_dict()
    assert data["verdict"] == CERTIFIED
    assert data["domain_conditions"]
    assert data["method_version"] == METHOD_VERSION
    rebuilt = RemainderCertificate(**data)
    assert validate_certificate(rebuilt) == CERTIFIED


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)


def test_documents_certified_is_not_hop_zero():
    readme = (PKG / "README.md").read_text(encoding="utf-8").lower()
    doc = (compile_mod.__doc__ or "").lower()
    blob = readme + "\n" + doc + "\n" + (compiler_pkg.__doc__ or "").lower()
    for tok in (
        "atom-local",
        "hop",
        "certified",
        "unknown",
        "domain",
        "fail",
    ):
        assert tok in blob, tok
    assert "not hop" in blob or "not a hop" in blob
