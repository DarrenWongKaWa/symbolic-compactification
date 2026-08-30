"""Integrity and exact-replay tests for response/tensor case packages."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from symbolic_compactification import ZERO, load_expression, run_summary


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = (
    ROOT / "research" / "representation_program_search" / "packages"
    / "response_tensor"
)
PACKAGE_IDS = {
    "rps-r-feshbach-optical-heff",
    "rps-t-barnes-rivers-dn",
    "rps-t-stf-son-rank3",
}
LOWERING_SCOPES = {
    "SYMBOLIC_SOURCE_OBJECT",
    "FIXED_SCIENTIFIC_INSTANCE",
    "FINITE_INDEX_DIAGNOSTIC",
}
PROPOSER_FORBIDDEN_KEYS = {
    "audited_depth",
    "gold",
    "operator",
    "operators",
    "program",
    "program_id",
    "reference",
    "reference_roles",
    "verdict",
}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _keys(child)


def test_package_set_and_manifests_are_complete_and_content_addressed():
    packages = {path.name for path in PACKAGE_ROOT.iterdir() if path.is_dir()}
    assert packages == PACKAGE_IDS

    for package_id in sorted(PACKAGE_IDS):
        package_root = PACKAGE_ROOT / package_id
        manifest = _json(package_root / "package.json")
        assert manifest["schema_version"] == "RPSCasePackageV1"
        assert manifest["package_id"] == package_id
        assert manifest["source_dossier_id"] == package_id
        assert manifest["package_status"] == "PACKAGE_READY"
        assert manifest["lowering_scope"] in LOWERING_SCOPES

        actual = {
            path.relative_to(package_root).as_posix(): _sha256(path)
            for path in sorted(package_root.rglob("*"))
            if path.is_file() and path.name != "package.json"
        }
        assert manifest["artifacts"] == actual
        assert manifest["member_count"] == len(list((package_root / "members").glob("*.txt")))


def test_source_catalogs_own_member_bytes_and_proposer_views_do_not_leak():
    for package_id in sorted(PACKAGE_IDS):
        package_root = PACKAGE_ROOT / package_id
        catalog = _json(package_root / "source_catalog.json")
        proposer = _json(package_root / "proposer_view.json")

        assert set(proposer) == {"assumptions", "source_catalog"}
        assert not (set(_keys(proposer)) & PROPOSER_FORBIDDEN_KEYS)
        assert proposer["source_catalog"] == {
            "members": catalog["members"],
            "symbols_path": catalog["symbols_path"],
        }

        member_ids = set()
        for member in catalog["members"]:
            assert member["member_id"] not in member_ids
            member_ids.add(member["member_id"])
            path = package_root / member["path"]
            assert path.is_file()
            assert not Path(member["path"]).is_absolute()
            assert _sha256(path) == member["sha256"]

        symbols = _json(package_root / catalog["symbols_path"])["symbols"]
        for member in catalog["members"]:
            record = load_expression(str(package_root / member["path"]), symbols)
            assert record.sha256 == member["sha256"]


def test_reference_program_hashes_and_retained_zero_sessions():
    for package_id in sorted(PACKAGE_IDS):
        package_root = PACKAGE_ROOT / package_id
        program = _json(package_root / "reference" / "program.json")
        program_id = program.pop("program_id")
        canonical = json.dumps(program, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == program_id

        obligations = _json(package_root / "reference" / "obligations.json")
        assert len(obligations["obligations"]) == 1
        obligation = obligations["obligations"][0]
        assert obligation["verdict"] == ZERO
        assert _sha256(package_root / obligation["current_path"]) == obligation["current_sha256"]
        assert _sha256(package_root / obligation["candidate_path"]) == obligation["candidate_sha256"]

        run_root = package_root / obligation["run_path"]
        summary = run_summary(run_root)
        assert summary["candidates_proposed"] == 1
        assert summary["proposer_mode"] == "MAIN_AGENT_ONLY"
        assert summary["verifier_calls"] == 1
        assert summary["zero_promotions"] == 1
        assert summary["nonzero_count"] == 0
        assert summary["unknown_count"] == 0
        assert (run_root / "final" / "FINAL_CERTIFIED_FORM.md").is_file()

        certified = _json(run_root / "steps" / "step_002.json")
        assert certified["verdict"] == ZERO
        assert certified["status"] == "CERTIFIED"
        assert certified["proof_status"] == "PROVEN"


def test_linear_combination_arguments_are_explicit_and_fail_closed():
    for package_id in sorted(PACKAGE_IDS):
        program = _json(PACKAGE_ROOT / package_id / "reference" / "program.json")
        for operator in program["operators"]:
            if operator["operator"] != "LINEAR_COMBINATION":
                continue
            arguments = operator["arguments"]
            assert isinstance(arguments, dict)
            assert set(arguments) == {"constant", "inputs"}
            assert isinstance(arguments["constant"], str)
            assert arguments["inputs"]
            for term in arguments["inputs"]:
                assert set(term) == {"coefficient", "input"}
                assert isinstance(term["coefficient"], str)
                assert isinstance(term["input"], str)

    feshbach = _json(
        PACKAGE_ROOT / "rps-r-feshbach-optical-heff" / "reference" / "program.json"
    )
    assert all(item["operator"] != "COMPOSE" for item in feshbach["operators"])
    assert feshbach["member_assignments"]["m004"] == "op_005"
    assert feshbach["member_assignments"]["m005"] == "op_005"


def test_assumptions_sources_and_finite_index_nonclaim():
    for package_id in sorted(PACKAGE_IDS):
        package_root = PACKAGE_ROOT / package_id
        assumptions = _json(package_root / "assumptions.json")
        source_manifest = _json(package_root / "source_manifest.json")
        package = _json(package_root / "package.json")

        assert assumptions["assumption_contract_status"] == "COMPLETE_AS_WRITTEN"
        labels = {
            item["label"]
            for field in ("derived", "lowering_assumptions", "scientific_assumptions")
            for item in assumptions[field]
        }
        assert labels <= {"DECLARED", "DERIVED"}
        assert source_manifest["source_dossier_id"] == package_id
        assert source_manifest["sources"]
        for source in source_manifest["sources"]:
            assert source.get("locator")
            assert source.get("equation_transcription") or source.get("equation_transcriptions") or source.get("equation_scope")
            assert source["artifact"].get("bytes_sha256") or source["artifact"].get("retrieval_status")

        if package_id.startswith("rps-t-"):
            assert package["lowering_scope"] == "FINITE_INDEX_DIAGNOSTIC"
            scope = source_manifest["package_derivation"]["scope"].lower()
            assert "diagnostic" in scope
            assert "not proof" in scope
        else:
            assert package["lowering_scope"] == "FIXED_SCIENTIFIC_INSTANCE"


def test_gap_registry_covers_both_fresh_dossier_clusters_without_guo():
    gap_registry = _json(PACKAGE_ROOT / "PACKAGING_GAPS.json")
    response_index = _json(
        ROOT / "research" / "representation_program_search" / "cases"
        / "response" / "index.json"
    )
    tensor_index = _json(
        ROOT / "research" / "representation_program_search" / "cases"
        / "tensor" / "index.json"
    )
    expected = {
        item["case_id"]
        for index in (response_index, tensor_index)
        for item in index["dossiers"]
    }
    cases = gap_registry["cases"]
    assert {item["case_id"] for item in cases} == expected
    assert len(cases) == len(expected) == 16
    assert not any("guo" in item["case_id"].lower() for item in cases)
    assert gap_registry["excluded_historical_policy"].startswith("No Guo")

    counts = {}
    for case in cases:
        counts[case["disposition"]] = counts.get(case["disposition"], 0) + 1
    assert gap_registry["summary"] == {**counts, "total": len(cases)}
    assert counts["PACKAGE_READY"] == 3
    assert counts["PACKAGING_GAP"] == 5
