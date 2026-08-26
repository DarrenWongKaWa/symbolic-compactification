"""Method v2 expansion and continue-after-ZERO contracts."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.method_v2.expand import expand_text, expand_and_verify
from research.method_v2.orchestrator import run_m0, run_method_v2
from symbolic_compactification import ZERO


def test_expand_named_master():
    text = expand_text(
        "A*Phi",
        {"Phi": "polygamma(0, zP) + polygamma(0, zM)"},
    )
    assert "Phi" not in text or "polygamma" in text
    assert "polygamma" in text


def test_expand_and_verify_thermal():
    cur = "A*polygamma(0, zP) + A*polygamma(0, zM)"
    expanded, r = expand_and_verify(
        cur, "A*Phi",
        {"Phi": "polygamma(0, zP) + polygamma(0, zM)"},
        [{"name": x, "real": True} for x in ("A", "zP", "zM")],
        [],
    )
    assert r.verdict == ZERO, (r.verdict, expanded, r.evidence)


def test_m1_continues_after_d1_and_names_master():
    cur = "A*polygamma(0, zP) + A*polygamma(0, zM)"
    syms = [{"name": x, "real": True} for x in ("A", "zP", "zM")]
    m0 = run_m0(cur, syms, [])
    m1 = run_method_v2(cur, syms, [], max_steps=4)
    assert m0["false_promotion"] is False
    assert m1["false_promotion"] is False
    assert m0["n_zero"] >= 1
    assert m1["named_aux_zero"] >= 1
    assert m1["extra_certified_after_first_zero"] >= 0
    assert m1["n_zero"] >= m0["n_zero"]


def test_m1_does_not_promote_drop_piecewise():
    cur = "Piecewise((K(x, y), Ne(x, y)), (K(x, x), True))"
    syms = [{"name": "x", "real": True}, {"name": "y", "real": True}]
    m1 = run_method_v2(cur, syms, ["K"], max_steps=4)
    assert m1["false_promotion"] is False
    assert m1["certified"] == cur or m1["n_zero"] == 0 or all(
        s["expanded"] != "K(x, y)" or s["verdict"] != ZERO for s in m1["steps"]
    )
