from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RPS = ROOT / "research" / "representation_program_search"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_final_report_has_exact_required_sections_and_one_decision() -> None:
    report = (RPS / "final" / "FINAL_SCIENTIFIC_VERDICT.md").read_text(
        encoding="utf-8"
    )
    assert report.startswith(
        "# Final Scientific Verdict — Verified Representation Program Search\n"
    )
    for index in range(1, 36):
        assert report.count(f"## {index}.") == 1
    decision = "F — STRUCTURED SEARCH ALSO FAILS TO SUPPORT REPRESENTATION INVENTION."
    assert report.count(decision) == 1
    assert "no S0–S7 or F0 scientific condition ran" in report
    assert "no live LLM call" in report
    assert "not evidence that" in report


def test_repertoire_has_exact_a_to_o_sections_and_no_search_cli_claim() -> None:
    report = (ROOT / "REPERTOIRE_V2.md").read_text(encoding="utf-8")
    assert report.startswith(
        "# Symbolic Compactification Repertoire — Evidence-Based V2\n"
    )
    for letter in "ABCDEFGHIJKLMNO":
        assert report.count(f"## {letter}.") == 1
    assert "Do not add `ssc search`" in report
    assert "Do not immediately create Representation Search V2" in report


def test_review_synthesis_binds_nine_unanimous_reviews() -> None:
    synthesis = _load(RPS / "reviews" / "final" / "REVIEW_SYNTHESIS.json")
    assert synthesis["schema_version"] == "RPSFinalReviewSynthesisV1"
    assert synthesis["review_count"] == 9
    assert synthesis["consensus_decision"] == "F"
    assert synthesis["review_status"] == "COMPLETE"
    reviews = synthesis["reviewers"]
    assert [review["id"] for review in reviews] == [f"R{i}" for i in range(1, 10)]
    assert {review["recommendation"] for review in reviews} == {"F"}
    for review in reviews:
        path = ROOT / review["path"]
        assert path.is_file()
        assert _sha256(path) == review["sha256"]


def test_closure_manifest_hashes_exact_artifacts_and_is_not_test_freeze() -> None:
    manifest = _load(RPS / "final" / "CLOSURE_MANIFEST.json")
    assert manifest["schema_version"] == "RPSClosureManifestV1"
    assert manifest["gate_decision"] == "GATE_BLOCKED"
    assert manifest["publication_decision"] == "F"
    assert manifest["scientific_treatment_started"] is False
    assert manifest["scientific_method_job_count"] == 0
    assert manifest["live_llm_call_count"] == 0
    assert manifest["fresh_test_frozen"] is False
    assert manifest["benchmark"]["status"] == "NOT_CREATED"
    assert manifest["benchmark"]["benchmark_hash"] is None
    assert manifest["manifest_role"] == "NEGATIVE_PROCESS_CLOSURE_NOT_TEST_FREEZE"
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.is_file()
        assert _sha256(path) == artifact["sha256"]


def test_no_rps_benchmark_or_test_freeze_was_fabricated() -> None:
    assert not (RPS / "DEV_MANIFEST.json").exists()
    assert not (RPS / "TEST_MANIFEST.json").exists()
    assert not (RPS / "final" / "FREEZE_MANIFEST.json").exists()


def test_capability_registry_separates_supported_from_unevaluated() -> None:
    registry = _load(ROOT / "CAPABILITIES.json")
    assert registry["schema_version"] == "SymbolicCompactificationCapabilitiesV2"
    capabilities = {item["name"]: item for item in registry["capabilities"]}
    assert capabilities["exact_equivalence_verification"]["status"] == "SUPPORTED"
    assert (
        capabilities["representation_grammar_v1_and_program_ir"]["status"]
        == "IMPLEMENTED_UNEVALUATED"
    )
    assert (
        capabilities["llm_legal_state_or_action_guidance"]["status"]
        == "IMPLEMENTED_UNEVALUATED"
    )
    assert (
        capabilities["r3_plus_representation_program_discovery"]["status"]
        == "NOT_SUPPORTED"
    )
    assert capabilities["guo_g0016_to_g0013"]["status"] == "SEALED"
    for capability in capabilities.values():
        assert len(capability["evidence_sha"]) == 40
        assert capability["known_failure_classes"]
        assert capability["verification_semantics"]


def test_negative_registry_preserves_all_closure_boundaries() -> None:
    registry = (ROOT / "NEGATIVE_RESULTS.md").read_text(encoding="utf-8")
    for index in range(1, 13):
        assert registry.count(f"## NR-{index:03d}") == 1
    for boundary in (
        "Free-form LLM representation advantage is not supported",
        "SOL is not uniformly helpful",
        "Guo G3 is sealed",
        "PACKAGING_GAP is not AI advantage or mathematical failure",
        "TYPE_ONLY is not an operational representation",
        "Missing calibration data is not an algorithmic null result",
    ):
        assert boundary in registry
