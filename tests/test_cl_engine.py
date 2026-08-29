"""Engine remainder must call remainder_ok. Domain comments are not ZERO."""
from __future__ import annotations

import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.engine import (  # noqa: E402
    sparse_laurent_limit,
)
from research.coefficient_laurent.remainder import remainder_ok  # noqa: E402
from research.coefficient_laurent.schema import (  # noqa: E402
    LEVEL_B,
    LEVEL_C,
    NONZERO,
    UNKNOWN,
    ZERO,
)

ENGINE = ROOT / "research" / "coefficient_laurent" / "engine.py"


def test_engine_source_calls_remainder_ok_no_guo_shortcut():
    src = ENGINE.read_text(encoding="utf-8")
    assert "remainder_ok" in src
    assert "energy arguments" not in src
    assert "1/2 + i E" not in src
    assert "Phi_Gamma" not in src


def test_holomorphic_polygamma_can_be_level_c():
    u = sympy.Symbol("u")
    src = sympy.polygamma(0, 1 + u)
    tgt = sympy.polygamma(0, 1)
    assert remainder_ok(1 + u, u) is True
    cert = sparse_laurent_limit(src, tgt, u, sympy.Integer(0))
    assert cert.remainder_verdict == ZERO
    assert cert.negative_coefficients_verdict == ZERO
    assert cert.constant_term_verdict == ZERO
    assert cert.final_verdict == ZERO
    assert cert.proof_level == LEVEL_C
    assert cert.used_full_together is False


def test_symbolic_alpha_blocks_level_c():
    u = sympy.Symbol("u")
    a = sympy.Symbol("a")
    src = sympy.polygamma(0, a + u)
    tgt = sympy.polygamma(0, a)
    assert remainder_ok(a + u, u) is False
    cert = sparse_laurent_limit(src, tgt, u, sympy.Integer(0))
    assert cert.remainder_verdict == UNKNOWN
    assert cert.final_verdict == UNKNOWN
    assert cert.final_verdict != ZERO
    assert cert.proof_level != LEVEL_C
    assert cert.used_full_together is False


def test_surviving_pole_still_nonzero():
    u = sympy.Symbol("u")
    f = sympy.Symbol("f")
    cert = sparse_laurent_limit(1 / u + f, f, u, sympy.Integer(0))
    assert cert.negative_coefficients_verdict == NONZERO
    assert cert.final_verdict == NONZERO
    assert cert.proof_level == LEVEL_B
