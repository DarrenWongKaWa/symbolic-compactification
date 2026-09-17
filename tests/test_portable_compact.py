"""Compactification entry: engine receipts, improvement axis, doctor."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "symbolic-compactification" / "scripts"


def load_script(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"ssc_compact_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_compact_verify_promotes_only_on_zero_and_records_improvement(tmp_path: Path):
    current = tmp_path / "current.txt"
    candidate = tmp_path / "candidate.txt"
    symbols = tmp_path / "symbols.json"
    current.write_text("x**2 + 2*x + 1\n", encoding="utf-8")
    candidate.write_text("(x + 1)**2\n", encoding="utf-8")
    symbols.write_text(
        json.dumps({"symbols": [{"name": "x", "real": True, "nonzero": False}]}),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "compact_verify.py"),
            "--current",
            str(current),
            "--candidate",
            str(candidate),
            "--symbols",
            str(symbols),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    receipt = json.loads((out / "verification.json").read_text(encoding="utf-8"))
    assert receipt["relation"]["verdict"] == "ZERO"
    assert receipt["improvement"]["verdict"] in {"IMPROVED", "NO_IMPROVEMENT", "DEPENDS"}
    assert (out / "result.tex").is_file()
    tex = (out / "result.tex").read_text(encoding="utf-8")
    assert "**" not in tex
    assert "^" in tex or "^{" in tex
    assert (out / "report.md").is_file()
    assert (out / "unresolved.md").is_file()


def test_compact_verify_rejects_sqrt_identity_over_reals(tmp_path: Path):
    current = tmp_path / "current.txt"
    candidate = tmp_path / "candidate.txt"
    symbols = tmp_path / "symbols.json"
    current.write_text("sqrt(x**2)\n", encoding="utf-8")
    candidate.write_text("x\n", encoding="utf-8")
    symbols.write_text(
        json.dumps({"symbols": [{"name": "x", "real": True, "nonzero": False}]}),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "compact_verify.py"),
            "--current",
            str(current),
            "--candidate",
            str(candidate),
            "--symbols",
            str(symbols),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    receipt = json.loads((out / "verification.json").read_text(encoding="utf-8"))
    assert receipt["relation"]["verdict"] != "ZERO"
    assert not (out / "result.tex").exists()


def test_name_wrapper_is_not_an_improvement(tmp_path: Path):
    current = tmp_path / "current.txt"
    candidate = tmp_path / "candidate.txt"
    symbols = tmp_path / "symbols.json"
    defs = tmp_path / "definitions.json"
    current.write_text("x**2 + 2*x + 1 + y**2 + 2*y + 1\n", encoding="utf-8")
    candidate.write_text("K\n", encoding="utf-8")
    symbols.write_text(
        json.dumps(
            {
                "symbols": [
                    {"name": "x", "real": True, "nonzero": False},
                    {"name": "y", "real": True, "nonzero": False},
                    {"name": "K", "real": True, "nonzero": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    defs.write_text(
        json.dumps({"K": "x**2 + 2*x + 1 + y**2 + 2*y + 1"}),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "compact_verify.py"),
            "--current",
            str(current),
            "--candidate",
            str(candidate),
            "--symbols",
            str(symbols),
            "--definitions",
            str(defs),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    receipt = json.loads((out / "verification.json").read_text(encoding="utf-8"))
    assert receipt["improvement"]["verdict"] == "NO_IMPROVEMENT"
    assert receipt["improvement"]["reason_code"] == "DEFINITION_WRAP"


def test_compact_input_error_does_not_keep_previous_result(tmp_path: Path):
    current = tmp_path / "current.txt"
    candidate = tmp_path / "candidate.txt"
    symbols = tmp_path / "symbols.json"
    current.write_text("x**2 + 2*x + 1\n", encoding="utf-8")
    candidate.write_text("(x + 1)**2\n", encoding="utf-8")
    symbols.write_text(
        json.dumps({"symbols": [{"name": "x", "real": True, "nonzero": False}]}),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    first = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "compact_verify.py"),
            "--current",
            str(current),
            "--candidate",
            str(candidate),
            "--symbols",
            str(symbols),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0
    assert (out / "result.tex").is_file()
    symbols.write_text("{not json", encoding="utf-8")
    second = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "compact_verify.py"),
            "--current",
            str(current),
            "--candidate",
            str(candidate),
            "--symbols",
            str(symbols),
            "--out",
            str(out),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert second.returncode != 0
    assert not (out / "result.tex").exists()
    record = json.loads((out / "verification.json").read_text(encoding="utf-8"))
    assert record["relation"]["verdict"] == "ERROR"


def test_doctor_reports_engine_or_reconstruction_mode():
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "doctor.py"), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode in {0, 1}
    data = json.loads(proc.stdout)
    assert data["mode"] in {"full_verification", "reconstruction_only", "broken"}
    if proc.returncode == 0:
        assert data["mode"] == "full_verification"
        assert data["self_check"]["identity"] == "ZERO"
        assert data["self_check"]["counterexample"] != "ZERO"
