"""Release security boundary: secrets never enter provenance or reports."""
from __future__ import annotations

import hashlib
import json

import pytest

from symbolic_compactification.provenance import (
    ProvenanceError,
    build_run_record,
    write_run_record,
)
from symbolic_compactification.reporting import render_final_report
from symbolic_compactification.security import (
    REDACTED,
    redact_public_data,
    redact_text,
)
from symbolic_compactification.verifier import verify_equivalent
from symbolic_compactification import initialize_workspace, verify_hypothesis


@pytest.mark.parametrize(
    ("label", "secret"),
    [
        ("OPENAI_API_KEY", "sk-proj-synthetic0123456789"),
        ("GITHUB_TOKEN", "ghp_synthetic0123456789012345"),
        ("SLACK_TOKEN", "xoxb-synthetic-0123456789"),
        ("GOOGLE_API_KEY", "AIzaSynthetic012345678901234567"),
        ("AWS_SECRET_ACCESS_KEY", "synthetic/aws/secret/value"),
        ("DATABASE_PASSWORD", "synthetic-database-password"),
        ("PRIVATE_CREDENTIAL", "synthetic-private-credential"),
    ],
)
def test_dotenv_style_sensitive_assignments_are_redacted(label, secret):
    rendered = redact_text(f"{label}={secret}\nSAFE_FLAG=true")
    assert secret not in rendered
    assert REDACTED in rendered
    assert "SAFE_FLAG=true" in rendered


def test_headers_urls_private_keys_and_jwts_are_redacted():
    secrets = {
        "basic": "dXNlcjpzeW50aGV0aWM=",
        "bearer": "synthetic-bearer-value",
        "cookie": "session=synthetic-cookie-value",
        "password": "synthetic-url-password",
        "jwt": "eyJsynthetic1.eyJsynthetic2.synthetic_signature",
        "pem": "synthetic-private-key-body",
    }
    text = (
        f"Authorization: Basic {secrets['basic']}\n"
        f"Proxy-Authorization: Bearer {secrets['bearer']}\n"
        f"Cookie: {secrets['cookie']}\n"
        f"postgres://user:{secrets['password']}@db.invalid/name\n"
        f"token={secrets['jwt']}\n"
        "-----BEGIN PRIVATE KEY-----\n"
        f"{secrets['pem']}\n"
        "-----END PRIVATE KEY-----"
    )
    rendered = redact_text(text)
    for secret in secrets.values():
        assert secret not in rendered
    assert rendered.count(REDACTED) >= 6


def test_public_data_redacts_sensitive_fields_without_stringifying_objects():
    class Dangerous:
        def __str__(self):  # pragma: no cover - invocation would fail the test
            raise AssertionError("must not stringify request/client objects")

        __repr__ = __str__

    payload = {
        "request": {
            "Authorization": "Bearer synthetic-header-secret",
            "api_key": "sk-synthetic-field-secret",
            "model": "local-test-model",
        },
        "exception": Dangerous(),
    }
    safe = redact_public_data(payload)
    blob = json.dumps(safe, sort_keys=True)
    assert "synthetic-header-secret" not in blob
    assert "sk-synthetic-field-secret" not in blob
    assert safe["request"]["Authorization"] == REDACTED
    assert safe["request"]["api_key"] == REDACTED
    assert safe["request"]["model"] == "local-test-model"
    assert safe["exception"] == "<Dangerous>"


def test_provenance_does_not_read_dotenv_and_resanitizes_before_write(
        tmp_path, monkeypatch):
    dotenv_secret = "synthetic-dotenv-secret-must-not-appear"
    environment_secret = "synthetic-environment-secret-must-not-appear"
    (tmp_path / ".env").write_text(
        f"UNRELATED_PRIVATE_VALUE={dotenv_secret}\n", encoding="utf-8")
    monkeypatch.setenv("UNRELATED_PRIVATE_VALUE", environment_secret)
    digest = hashlib.sha256(b"x\n").hexdigest()
    record = build_run_record(
        input_hashes={"notes/context.md": digest},
        expression_hashes={"expressions/current.txt": digest},
        hypothesis_hash=digest,
        assumptions_hash=digest,
        verifier_route="python_sympy_exact_v1",
        result="UNKNOWN",
        runtime_seconds=0.1,
        warnings=["safe warning"],
        run_id="security-test",
        timestamp="2026-08-31T04:05:06Z",
        git_commit="a" * 40,
        installed_dependencies={"sympy": "1.14.0"},
    )
    # Simulate a caller mutating the in-memory record before persistence.
    record["warnings"] = [
        "provider failed: Authorization: Bearer synthetic-runtime-secret"]
    path = write_run_record(tmp_path / "runs", record)
    blob = path.read_text(encoding="utf-8")
    assert "synthetic-runtime-secret" not in blob
    assert dotenv_secret not in blob
    assert environment_secret not in blob
    assert REDACTED in blob


@pytest.mark.parametrize("overrides", [
    {"input_hashes": {
        "notes/sk-synthetic-secret-filename": hashlib.sha256(
            b"x").hexdigest(),
    }},
    {"installed_dependencies": {"sk-synthetic-secret-package": "1.0"}},
])
def test_provenance_rejects_credential_shaped_map_keys(overrides):
    digest = hashlib.sha256(b"x\n").hexdigest()
    values = {
        "input_hashes": {"notes/context.md": digest},
        "expression_hashes": {"expressions/current.txt": digest},
        "hypothesis_hash": digest,
        "assumptions_hash": digest,
        "verifier_route": "python_sympy_exact_v1",
        "result": "UNKNOWN",
        "runtime_seconds": 0.1,
        "run_id": "security-map-key-test",
        "timestamp": "2026-08-31T04:05:06Z",
        "git_commit": "a" * 40,
        "installed_dependencies": {"sympy": "1.14.0"},
    }
    values.update(overrides)
    with pytest.raises(ProvenanceError, match="PROVENANCE_UNSAFE_VALUE"):
        build_run_record(**values)


def test_certified_report_redacts_untrusted_manifest_metadata(tmp_path):
    run = tmp_path / "run"
    (run / "final").mkdir(parents=True)
    text = "x + 1"
    (run / "final" / "current.json").write_text(json.dumps({
        "text": text,
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
        "symbols": [{"name": "x", "real": True, "nonzero": False}],
        "functions": [],
    }), encoding="utf-8")
    metadata_secret = "sk-synthetic-report-secret"
    (run / "manifest.json").write_text(json.dumps({
        "run_id": f"Authorization: Bearer {metadata_secret}",
        "repository_version": f"version={metadata_secret}",
        "engine_version": "0.3.0",
        "agent_protocol_version": "0.3.0",
        "engine_git_sha": "a" * 40,
        "steps": [],
    }), encoding="utf-8")

    report = render_final_report(run)
    artifact = (run / "final" / "FINAL_CERTIFIED_FORM.md").read_text(
        encoding="utf-8")
    assert metadata_secret not in json.dumps(report, default=str)
    assert metadata_secret not in artifact
    assert REDACTED in artifact
    assert report["certified_text"] == text


def test_redactor_rejects_non_strings_instead_of_using_repr():
    with pytest.raises(TypeError, match="requires a string"):
        redact_text(RuntimeError("Authorization: Bearer synthetic-secret"))


def test_workspace_summary_and_report_redact_metadata_and_omit_context_contents(
        tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    secret = "sk-synthetic-workspace-report-secret"
    project = root / "project.yaml"
    project.write_text(
        project.read_text(encoding="utf-8").replace(
            "Test an exact symbolic hypothesis without modifying source files.",
            secret,
        ),
        encoding="utf-8",
    )
    (root / "notes/research_notes.md").write_text(
        f"note-only-content {secret}\n", encoding="utf-8")
    (root / "references/README.md").write_text(
        f"reference-only-content {secret}\n", encoding="utf-8")
    hypothesis_path = root / "hypotheses/hypothesis.json"
    hypothesis = json.loads(hypothesis_path.read_text(encoding="utf-8"))
    hypothesis["latent_object"] = secret
    hypothesis["instance_maps"] = {"api_key": secret}
    hypothesis_path.write_text(json.dumps(hypothesis), encoding="utf-8")

    result = verify_hypothesis(root, run_id="summary-redaction")
    blob = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(result.run_directory.iterdir())
        if path.is_file()
    )

    assert secret not in blob
    assert "note-only-content" not in blob
    assert "reference-only-content" not in blob
    assert REDACTED in blob


@pytest.mark.parametrize(("current", "candidate"), [
    ("x + 1", "1 + x"),
    ("not valid syntax", "x"),
])
def test_verifier_evidence_cannot_persist_secrets_from_assumptions(
        current, candidate):
    secret = "sk-synthetic-assumption-secret"
    result = verify_equivalent(
        current,
        candidate,
        ["x"],
        assumptions={
            "x_nonzero": True,
            "api_key": secret,
            "request": {"Authorization": f"Bearer {secret}"},
        },
    )
    blob = json.dumps(result.to_dict(), sort_keys=True)
    assert secret not in blob
    assert REDACTED in blob
