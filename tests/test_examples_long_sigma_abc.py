"""Ingest the real Guo σ_abc DC source. Input only — no compact theorem."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from symbolic_compactification import ZERO, verify_equivalent
from symbolic_compactification.adapters.wolfram_text import (
    extract_expression_text,
    translate_wolfram_text,
)
from symbolic_compactification.cli import load_namespace_file, main as cli_main
from symbolic_compactification.structure import structure_summary

LONG = Path(__file__).resolve().parent.parent / "examples" / "long"
SOURCE = LONG / "Guo_Sigma_abc_dc_exact.txt"
EXPECTED_SHA256 = (
    "63742cc4e6bf401dd48e258ecb86676b0d7570cc075cae38b91dc188652afc44"
)


def test_long_source_bytes_match_lock():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert digest == EXPECTED_SHA256
    assert EXPECTED_SHA256 in (LONG / "SOURCE.md").read_text(encoding="utf-8")


def test_long_wolfram_inspect_reports_structure(capsys):
    code = cli_main([
        "inspect", str(SOURCE), "--format", "wolfram", "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    summary = payload["structure_summary"]
    assert summary["sums"] == 4
    assert summary["piecewise"] == 4
    assert summary["piecewise_branches"] == 14
    assert set(summary["indexed_names"]) == {"epsilon", "h1", "h2"}
    assert summary["count_ops"] == 3911
    native = translate_wolfram_text(
        extract_expression_text(SOURCE.read_text(encoding="utf-8"))).text
    assert payload["text"] == native
    assert payload["translated"] == native
    assert len(payload["preview"]) <= 204
    assert payload["preview"].endswith(" ...")


def test_long_translated_text_tautology_is_zero():
    """Identity check on the translated native text. Not a compactification."""
    translated = translate_wolfram_text(
        extract_expression_text(SOURCE.read_text(encoding="utf-8")))
    symbols, functions = load_namespace_file(str(LONG / "symbols.json"))
    result = verify_equivalent(
        translated.text, translated.text, symbols, functions=functions)
    assert result.verdict == ZERO
    assert result.simplified_residual == "0"
    summary = structure_summary(translated.expr)
    assert summary["sums"] == 4
    assert "polygamma" not in summary["indexed_names"]
