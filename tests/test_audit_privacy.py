"""Privacy firewall tests. Synthetic denylist tokens only; no manuscript text."""
from __future__ import annotations

from pathlib import Path

import pytest

from symbolic_compactification.audit.privacy import (
    PRIVATE_DENYLIST_RELPATH,
    PRIVATE_OFFLINE_ENV,
    PRIVATE_PATH_PREFIXES,
    PRIVATE_VALIDATION_DIRNAME,
    REFUSED_NETWORK_PREFIXES,
    is_private_relpath,
    load_denylist,
    refuse_network_if_private_offline,
    refuse_proposer_if_private_offline,
    scan_paths,
    scan_text_for_denylist,
)
from symbolic_compactification.audit.schema import AuditError

SYNTHETIC_TOKEN = "SYNTHETIC_DENYLIST_TOKEN_ALPHA"
_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_frozen_privacy_constants_are_intact():
    assert PRIVATE_OFFLINE_ENV == "SSC_PRIVATE_OFFLINE"
    assert PRIVATE_VALIDATION_DIRNAME == ".private_validation"
    assert PRIVATE_DENYLIST_RELPATH == ".private_validation/private_denylist.txt"
    assert PRIVATE_PATH_PREFIXES == (".private_validation/",)
    assert REFUSED_NETWORK_PREFIXES == ("http://", "https://", "ftp://")


def test_private_offline_refuses_network_and_proposer(monkeypatch):
    monkeypatch.setenv(PRIVATE_OFFLINE_ENV, "1")
    with pytest.raises(AuditError) as network:
        refuse_network_if_private_offline("https://example.invalid/resource")
    assert network.value.code == "PRIVATE_OFFLINE_NETWORK_REFUSED"
    with pytest.raises(AuditError) as proposer:
        refuse_proposer_if_private_offline()
    assert proposer.value.code == "PRIVATE_OFFLINE_PROPOSER_DISABLED"
    refuse_network_if_private_offline("/local/deterministic/path")


def test_private_offline_disabled_allows_network_and_proposer(monkeypatch):
    monkeypatch.delenv(PRIVATE_OFFLINE_ENV, raising=False)
    refuse_network_if_private_offline("https://example.invalid/resource")
    refuse_proposer_if_private_offline()
    monkeypatch.setenv(PRIVATE_OFFLINE_ENV, "0")
    refuse_network_if_private_offline("http://example.invalid/resource")
    refuse_proposer_if_private_offline()


def test_is_private_relpath_classifies_validation_vs_public_reports():
    assert is_private_relpath(".private_validation/x") is True
    assert is_private_relpath("reports/TABLE_VERIFIED.md") is False


def test_load_denylist_missing_is_empty_public_ci(tmp_path):
    assert not (tmp_path / PRIVATE_DENYLIST_RELPATH).exists()
    assert load_denylist(tmp_path) == ()


def test_load_denylist_reads_synthetic_tokens_and_skips_comments(tmp_path):
    denylist_path = tmp_path / PRIVATE_DENYLIST_RELPATH
    denylist_path.parent.mkdir(parents=True)
    denylist_path.write_text(
        "# not a token\n\n"
        f"{SYNTHETIC_TOKEN}\n"
        "SYNTHETIC_DENYLIST_TOKEN_BETA\n",
        encoding="utf-8",
    )
    assert load_denylist(tmp_path) == (
        SYNTHETIC_TOKEN,
        "SYNTHETIC_DENYLIST_TOKEN_BETA",
    )


def test_scan_text_for_denylist_hits_synthetic_token():
    hits = scan_text_for_denylist(
        f"public fixture contains {SYNTHETIC_TOKEN} only",
        (SYNTHETIC_TOKEN, "SYNTHETIC_DENYLIST_TOKEN_BETA"),
    )
    assert hits == (SYNTHETIC_TOKEN,)
    assert scan_text_for_denylist("no listed token here", (SYNTHETIC_TOKEN,)) == ()


def test_gitignore_contains_private_validation_directory():
    gitignore = (_REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".private_validation/" in gitignore


def test_scan_paths_skips_missing_denylist(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "TABLE_VERIFIED.md").write_text(
        f"would match {SYNTHETIC_TOKEN} if a denylist existed\n",
        encoding="utf-8",
    )
    assert scan_paths(tmp_path) is False


def test_scan_paths_hits_synthetic_token_in_public_file(tmp_path):
    denylist_path = tmp_path / PRIVATE_DENYLIST_RELPATH
    denylist_path.parent.mkdir(parents=True)
    denylist_path.write_text(f"{SYNTHETIC_TOKEN}\n", encoding="utf-8")
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "TABLE_VERIFIED.md").write_text(
        f"row {SYNTHETIC_TOKEN}\n",
        encoding="utf-8",
    )
    assert scan_paths(tmp_path) is True


def test_scan_paths_skips_private_validation_tree(tmp_path):
    denylist_path = tmp_path / PRIVATE_DENYLIST_RELPATH
    denylist_path.parent.mkdir(parents=True)
    denylist_path.write_text(f"{SYNTHETIC_TOKEN}\n", encoding="utf-8")
    (denylist_path.parent / "local_notes.txt").write_text(
        f"{SYNTHETIC_TOKEN}\n",
        encoding="utf-8",
    )
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "TABLE_VERIFIED.md").write_text("public row\n", encoding="utf-8")
    assert scan_paths(tmp_path) is False
