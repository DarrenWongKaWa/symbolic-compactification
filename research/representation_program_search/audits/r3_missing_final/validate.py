"""Replay the immutable facts of the final bounded fresh-R3 mining audit."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[4]
AUDIT_DIR = Path(__file__).resolve().parent
AUDIT = AUDIT_DIR / "R3_MISSING.json"
AUTHORITY_HEAD = "bcb43e25c0b529fcf172d545e852577848d2135c"
CORPUS_DIGEST = "cc8dbfd73a27d69d86763f9e429cae1f2e02e8f0c5aee9cd63e70be75dcb63cc"
CORPUS_PATTERNS = (
    "research/assumption_complete_representation/cases/**/*.json",
    "research/representation_invention/bench/tasks/dev/*.json",
    "research/representation_invention/bench/tasks/test/*.json",
    "research/representation_program_search/packages/**/package.json",
    "research/representation_program_search/packages/**/source_manifest.json",
)
EXPECTED_COUNTS = {
    "historical_case_json": 47,
    "old_dev_tasks": 18,
    "old_test_tasks": 14,
    "current_package_manifests": 19,
    "current_source_manifests": 19,
    "total": 117,
}
EXPECTED_SOURCES = {
    "1509.05030v2": (
        "46e50fdfdeaba67d7c0f6d83755b5fdfaf5ce0541e816e854e03bb46aa5c0d13",
        "28b21a27bc43480222964f897a4925a32a2fcf22ccd33d6ae3fabfe78e9df694",
        70308,
        ((502, 529), (1286, 1354), (2088, 2105)),
    ),
    "2306.15814v1": (
        "c715d8f193772813dbc492a51c5c878a657b0720345f58e303459e04c010fcf4",
        "bae495f1f0f061517f9a577d950f8c8c813e7b98547e570222a87788ebe39082",
        82954,
        ((630, 688), (1140, 1214), (1215, 1244)),
    ),
    "1504.00960v2": (
        "783b0493ddbff7bf4b60c2fea93e50cbc4a207736ad106f93e77461ec83dea04",
        "718206b68100fab7d8d936173d2495651f86168e8d75560650ef93728adc6905",
        73531,
        ((470, 496), (640, 720), (730, 770), (897, 923)),
    ),
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class R3MissingAuditError(ValueError):
    """An immutable audit fact failed replay."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise R3MissingAuditError(code)


def _load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, Mapping), f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _git_bytes(commit: str, path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    _require(completed.returncode == 0, f"AUTHORITY_PATH_UNAVAILABLE:{path}")
    return completed.stdout


def _authority_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", AUTHORITY_HEAD],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    _require(completed.returncode == 0, "AUTHORITY_COMMIT_UNAVAILABLE")
    paths = []
    for relative in completed.stdout.splitlines():
        if any(fnmatch(relative, pattern) for pattern in CORPUS_PATTERNS):
            paths.append(relative)
    return sorted(set(paths))


def _corpus_digest(paths: list[str]) -> str:
    rows = []
    for relative in paths:
        digest = hashlib.sha256(_git_bytes(AUTHORITY_HEAD, relative)).hexdigest()
        rows.append(f"{relative}\t{digest}")
    return hashlib.sha256(("\n".join(rows) + "\n").encode("utf-8")).hexdigest()


def _source_gate(audit: Mapping[str, Any]) -> None:
    screens = audit.get("screened_families")
    _require(isinstance(screens, list) and len(screens) == 3, "SCREEN_COUNT")
    found = set()
    for screen in screens:
        _require(isinstance(screen, Mapping), "SCREEN_OBJECT")
        source = screen.get("primary_source")
        _require(isinstance(source, Mapping), "PRIMARY_SOURCE_OBJECT")
        version = source.get("arxiv_id_version")
        _require(version in EXPECTED_SOURCES and version not in found, f"SOURCE_VERSION:{version}")
        found.add(version)
        archive_hash, tex_hash, byte_count, ranges = EXPECTED_SOURCES[version]
        _require(source.get("archive_url") == f"https://export.arxiv.org/e-print/{version}", f"SOURCE_URL:{version}")
        _require(source.get("archive_sha256") == archive_hash, f"ARCHIVE_HASH:{version}")
        _require(source.get("tex_sha256") == tex_hash, f"TEX_HASH:{version}")
        _require(source.get("tex_byte_count") == byte_count, f"TEX_BYTES:{version}")
        locators = screen.get("locators")
        _require(isinstance(locators, list) and len(locators) == len(ranges), f"LOCATOR_COUNT:{version}")
        actual_ranges = []
        for locator in locators:
            _require(isinstance(locator, Mapping), f"LOCATOR_OBJECT:{version}")
            value = locator.get("lines")
            _require(isinstance(value, str) and re.fullmatch(r"[1-9][0-9]*-[1-9][0-9]*", value) is not None, f"LOCATOR_RANGE:{version}")
            start, end = (int(item) for item in value.split("-"))
            _require(start <= end, f"LOCATOR_ORDER:{version}")
            actual_ranges.append((start, end))
            _require(isinstance(locator.get("sha256"), str) and HEX64.fullmatch(locator["sha256"]) is not None, f"LOCATOR_HASH:{version}")
            _require(isinstance(locator.get("content"), str) and locator["content"], f"LOCATOR_CONTENT:{version}")
        _require(tuple(actual_ranges) == ranges, f"LOCATOR_SET:{version}")
        _require(screen.get("freshness_assessment") == "FAIL", f"FRESHNESS_FAIL_CLOSED:{version}")
        _require(screen.get("disposition") == "REJECT_NO_PACKAGE", f"DISPOSITION:{version}")
        codes = screen.get("rejection_codes")
        _require(isinstance(codes, list) and any("SUPERFAMILY" in code for code in codes), f"SUPERFAMILY_AUDIT:{version}")
    _require(found == set(EXPECTED_SOURCES), "SOURCE_SET")


def _duplicate_gate(audit: Mapping[str, Any]) -> None:
    duplicate = audit.get("duplicate_audit")
    _require(isinstance(duplicate, Mapping), "DUPLICATE_AUDIT_OBJECT")
    _require(duplicate.get("authority_commit") == AUTHORITY_HEAD, "DUPLICATE_AUTHORITY")
    _require(tuple(duplicate.get("corpus_patterns", ())) == CORPUS_PATTERNS, "CORPUS_PATTERNS")
    _require(duplicate.get("file_counts") == EXPECTED_COUNTS, "CORPUS_DECLARED_COUNTS")
    _require(duplicate.get("canonical_path_hash_rows_sha256") == CORPUS_DIGEST, "CORPUS_DECLARED_DIGEST")
    paths = _authority_paths()
    _require(len(paths) == EXPECTED_COUNTS["total"], "CORPUS_REPLAY_COUNT")
    _require(_corpus_digest(paths) == CORPUS_DIGEST, "CORPUS_REPLAY_DIGEST")
    controls = duplicate.get("key_controls")
    _require(isinstance(controls, list) and len(controls) == 7, "KEY_CONTROL_COUNT")
    identities = {}
    for control in controls:
        _require(isinstance(control, Mapping), "KEY_CONTROL_OBJECT")
        identity = control.get("identity")
        path = control.get("path")
        expected = control.get("sha256")
        _require(isinstance(identity, str) and isinstance(path, str), "KEY_CONTROL_FIELDS")
        _require(isinstance(expected, str) and HEX64.fullmatch(expected) is not None, f"KEY_CONTROL_HASH_FORMAT:{identity}")
        actual = hashlib.sha256(_git_bytes(AUTHORITY_HEAD, path)).hexdigest()
        _require(actual == expected, f"KEY_CONTROL_HASH:{identity}")
        identities[identity] = control
    _require(identities["mp-opitz-dd-01"]["relation"] == "DIRECT_GENERIC_SUPERFAMILY", "OPITZ_RELATION")
    manifest = json.loads(_git_bytes(AUTHORITY_HEAD, "research/assumption_complete_representation/TEST_MANIFEST.json"))
    _require("mp-opitz-dd-01" in manifest["CHALLENGE"], "OPITZ_PREVIOUS_TEST")
    opitz = json.loads(_git_bytes(AUTHORITY_HEAD, identities["mp-opitz-dd-01"]["path"]))
    _require("nodes, not necessarily distinct" in opitz["expression_sketch"].casefold(), "OPITZ_ARBITRARY_NODES")
    _require("hermite" in opitz["latent_structure"].casefold(), "OPITZ_HERMITE_SCOPE")


def validate() -> dict[str, Any]:
    """Replay fail-closed source and duplicate evidence without network access."""
    audit = _load(AUDIT)
    _require(audit.get("schema_version") == "RPSFreshR3MissingAuditV1", "AUDIT_SCHEMA")
    _require(audit.get("authority_head") == AUTHORITY_HEAD, "AUDIT_AUTHORITY")
    _require(audit.get("status") == "R3_MISSING", "AUDIT_STATUS")
    _require(audit.get("candidate_created") is False, "CANDIDATE_CREATED")
    _require(audit.get("candidate_package") is None, "CANDIDATE_PACKAGE")
    _require(audit.get("admission_ready_count") == 0, "ADMISSION_COUNT")
    scope = audit.get("scope")
    _require(isinstance(scope, Mapping), "SCOPE_OBJECT")
    _require(scope.get("method_calls_made") is False, "METHOD_CALL")
    _require(scope.get("verifier_calls_made") is False, "VERIFIER_CALL")
    _require(scope.get("historical_test_metadata_audited") is True, "HISTORICAL_TEST_AUDIT")
    _require(scope.get("fresh_test_hidden_identity_accessed") is False, "FRESH_TEST_ACCESS")
    _require(scope.get("test_artifact_modified") is False, "TEST_MODIFICATION")
    _source_gate(audit)
    _duplicate_gate(audit)
    mechanical = audit.get("mechanical_evidence")
    _require(isinstance(mechanical, Mapping), "MECHANICAL_OBJECT")
    _require(mechanical.get("public_case_loader") == "NOT_RUN_NO_SURVIVOR", "PUBLIC_LOADER_STATUS")
    _require(mechanical.get("m1_compilation") == "NOT_RUN_NO_SURVIVOR", "M1_STATUS")
    _require(mechanical.get("session_receipts") == "NOT_CREATED_NO_SURVIVOR", "SESSION_STATUS")
    return {
        "admission_ready_count": 0,
        "authority_head": AUTHORITY_HEAD,
        "corpus_file_count": EXPECTED_COUNTS["total"],
        "screened_source_count": len(EXPECTED_SOURCES),
        "status": "VALID_R3_MISSING_AUDIT",
        "verdict": "R3_MISSING",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
