"""LLM abstraction layer contracts. No live API. No gold leakage."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.leak import leak_hits
from research.llm_abstraction.packetizer import (
    basic_summary,
    observe_cached,
    packetize,
    render_packets,
)
from research.llm_abstraction.parser import parse_model_output
from research.llm_abstraction.quality import flag_unnecessary
from research.llm_abstraction.schema import (
    LLMStructureHypothesis,
    PARSE_FAILURE,
    OK,
    REQUIRED_FIELDS,
)
from research.llm_abstraction.secrets import redact_text, sanitize
from research.llm_abstraction.tasks import load_calibration, public_item
from research.abstraction_invention.prototype.orchestrator import run_b9_frozen


def _ok_payload(**over):
    base = {
        "hypothesis_type": "parameterized_family",
        "target_members": ["V(p)*G0(p)*V(p)", "V(q)*G0(q)*V(q)"],
        "latent_object": "V(theta)*G0(theta)*V(theta)",
        "parameters": ["theta"],
        "operators": [{"member": "V(p)*G0(p)*V(p)", "O": "identity"}],
        "instance_maps": [{"member": "V(p)*G0(p)*V(p)", "theta": {"theta": "p"}}],
        "construction_plan": "substitute theta",
        "required_assumptions": [],
        "proof_obligations": ["V(p)*G0(p)*V(p) - F(p) = 0"],
        "rationale": "same skeleton, different parameter",
        "confidence": 0.7,
    }
    base.update(over)
    return {"abstain": False, "hypotheses": [base]}


def test_parser_ok():
    r = parse_model_output(json.dumps(_ok_payload()))
    assert r.parse_status == OK
    assert r.hypotheses[0].hypothesis_type == "parameterized_family"


def test_parser_fence_format_only():
    raw = "```json\n" + json.dumps(_ok_payload()) + "\n```"
    r = parse_model_output(raw)
    assert r.parse_status == OK


def test_missing_latent_is_parse_failure():
    p = _ok_payload()
    del p["hypotheses"][0]["latent_object"]
    r = parse_model_output(json.dumps(p))
    assert r.hypotheses[0].parse_status == PARSE_FAILURE
    assert "latent_object" in (r.hypotheses[0].parse_error or "")


def test_unknown_type_not_silently_mapped():
    r = parse_model_output(json.dumps(_ok_payload(hypothesis_type="family")))
    assert r.hypotheses[0].parse_status == PARSE_FAILURE
    assert "unknown_hypothesis_type" in (r.hypotheses[0].parse_error or "")


def test_confidence_not_clamped():
    r = parse_model_output(json.dumps(_ok_payload(confidence=1.5)))
    assert r.hypotheses[0].parse_status == PARSE_FAILURE


def test_unnecessary_interpolation_flagged():
    hyp = LLMStructureHypothesis(
        hypothesis_type="parameterized_family",
        target_members=["V(p)*G0(p)*V(p)", "V(q)*G0(q)*V(q)"],
        latent_object="V(z)*G0(z)*V(z)",
        parameters=["z"],
        operators=[],
        instance_maps=[],
        construction_plan="geodesic interpolation between p and q",
        required_assumptions=[],
        proof_obligations=[],
        rationale="affine combination in a latent space",
        confidence=0.4,
    )
    flags = flag_unnecessary(hyp)
    assert "UNNECESSARY_STRUCTURE" in flags


def test_packets_no_interpretation():
    b = observe_cached(
        "K(n)*a(n) + K(n)*b(n)",
        [{"name": "n", "real": True}], ["K", "a", "b"],
        backends="relations", timeout_s=12.0,
    )
    pk = packetize(b, cap=10)
    txt = render_packets(pk)
    assert not leak_hits(txt)
    sm = basic_summary(
        "K(n)*a(n) + K(n)*b(n)",
        [{"name": "n", "real": True}], ["K", "a", "b"],
    )
    assert sm["count_ops"] >= 1


def test_public_item_strips_gold():
    items = load_calibration()
    assert items
    for it in items:
        pub = public_item(it)
        blob = json.dumps(pub)
        assert "gold_types" not in blob
        assert "gold_members" not in blob
        assert "hidden_gold" not in blob
        assert "Fborn" not in blob
        assert "Phi_Gamma" not in blob


def test_sanitize_redacts_key_material():
    assert "REDACTED" in redact_text("Authorization: Bearer sk-abcdefghijklmnopqrstuv")
    s = sanitize({"api_key": "sk-abcdefghijklmnopqrstuv", "ok": 1})
    assert s["api_key"] == "REDACTED"
    assert s["ok"] == 1


def test_required_fields_frozen():
    assert "latent_object" in REQUIRED_FIELDS
    assert "proof_obligations" in REQUIRED_FIELDS


def test_frozen_b9_still_importable():
    item = {
        "id": "toy",
        "current": "K(n)*a(n)+K(n)*b(n)",
        "symbols": [{"name": "n", "real": True}],
        "functions": ["K", "a", "b"],
        "split": "dev",
    }
    run = run_b9_frozen(item)
    assert run.get("method") == "B9_frozen" or run.get("baseline") == "B9"
