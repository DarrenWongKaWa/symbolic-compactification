"""reproduce.sh must fail when packaged records differ from a fresh replay."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from symbolic_compactification import cli
from symbolic_compactification.audit.replay_compare import compare_records, load_record_file

pytestmark = pytest.mark.derivation_audit_release_critical

DEMO = Path(__file__).resolve().parents[1] / "tests/fixtures/audit_demos/M"


@pytest.fixture(scope="module")
def package(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("replay") / "M"
    shutil.copytree(DEMO, root)
    assert cli.main(["audit", "verify", str(root)]) == 2      # NONZERO rows exist
    assert cli.main(["audit", "package", str(root)]) == 0
    return root / "reviewer-verification-package"


def _replay(package_dir: Path, tmp_path: Path) -> subprocess.CompletedProcess:
    copy = tmp_path / "pkg"
    shutil.copytree(package_dir, copy)
    return copy, subprocess.run(["sh", str(copy / "reproduce.sh")],
                                capture_output=True, text=True, timeout=600)


def test_reproduce_script_compares_and_tolerates_nonzero_rows(package):
    text = (package / "reproduce.sh").read_text(encoding="utf-8")
    assert 'ssc_audit verify "$REPLAY" || test $? -eq 2' in text
    assert "ssc_audit compare" in text and "machine_records.json" in text


def test_clean_package_replays_to_matching_records(package, tmp_path):
    _, done = _replay(package, tmp_path)
    assert done.returncode == 0, done.stderr[-2000:]
    assert "REPLAY_MATCHES" in done.stdout


def test_forged_status_and_conclusion_fail_the_replay(package, tmp_path):
    copy = tmp_path / "forged"
    shutil.copytree(package, copy)
    records = copy / "machine_results/machine_records.json"
    data = json.loads(records.read_text(encoding="utf-8"))
    for row in data:
        if row["edge_id"] == "M.fermion-bubble-wrong-sign":
            row["status"] = row["result"] = "CERTIFIED_BY_RULE"
        if row["edge_id"] == "M.fermion-bubble":
            row["rule_certificate"]["conclusion"] = "T*sum_n F(i*w_n) = 999999"
    records.write_text(json.dumps(data), encoding="utf-8")
    done = subprocess.run(["sh", str(copy / "reproduce.sh")],
                          capture_output=True, text=True, timeout=600)
    assert done.returncode != 0
    assert "REPLAY_MISMATCH" in done.stdout
    problems = compare_records(load_record_file(records),
                               load_record_file(package / "machine_results/machine_records.json"))
    fields = {(p["edge_id"], p.get("field")) for p in problems}
    assert ("M.fermion-bubble", "conclusion") in fields
    assert ("M.fermion-bubble-wrong-sign", "status") in fields
