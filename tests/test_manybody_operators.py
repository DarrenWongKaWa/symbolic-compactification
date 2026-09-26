"""Free-algebra operator identities and Langreth rules (Keldysh algebra)."""
from __future__ import annotations

import json

import pytest

from symbolic_compactification import cli
from symbolic_compactification.manybody import verify_langreth, verify_operator_identity

pytestmark = pytest.mark.release_critical

LINDBLAD = "-I*Comm(H, rho) + c*rho*Dag(c) - Rational(1, 2)*Anti(Dag(c)*c, rho)"
EFFECTIVE = "-I*((H - I/2*Dag(c)*c)*rho - rho*Dag(H - I/2*Dag(c)*c)) + c*rho*Dag(c)"


def op(lhs, rhs, **kw):
    return verify_operator_identity(lhs, rhs, **kw)["verdict"]


def test_lindblad_equals_effective_hamiltonian_plus_jumps():
    kw = {"operators": ["H", "rho", "c"], "hermitian": ["H", "rho"]}
    assert op(LINDBLAD, EFFECTIVE, **kw) == "ZERO"
    assert op(LINDBLAD, EFFECTIVE.replace("- I/2", "+ I/2"), **kw) == "NONZERO"


def test_commutator_algebra():
    ops = {"operators": ["A", "B", "C"]}
    assert op("Comm(A, Comm(B, C)) + Comm(B, Comm(C, A)) + Comm(C, Comm(A, B))", "0", **ops) == "ZERO"
    assert op("Comm(A*B, C)", "A*Comm(B, C) + Comm(A, C)*B", **ops) == "ZERO"
    assert op("Comm(A*B, C)", "Comm(B, C)*A + B*Comm(A, C)", **ops) == "NONZERO"


def test_parser_refuses_undeclared_names_inverses_and_dunders():
    for text in ("A*D", "A/B", "A.__class__", "exec(A)"):
        result = verify_operator_identity(text, "0", operators=["A", "B"])
        assert result["verdict"] == "UNKNOWN", text


@pytest.mark.parametrize("product, component, claim", [
    (["A", "B"], "less", "A_R*B_less + A_less*B_A"),                        # Jauho (27)
    (["A", "B"], "greater", "A_R*B_greater + A_greater*B_A"),
    (["A", "B", "C"], "less", "A_R*B_R*C_less + A_R*B_less*C_A + A_less*B_A*C_A"),  # (28)
    (["A", "B"], "R", "A_R*B_R"),                                           # (29)
    (["A", "B"], "K", "A_R*B_K + A_K*B_A"),
])
def test_langreth_rules_are_certified(product, component, claim):
    result = verify_langreth(product, component, claim)
    assert result["status"] == "CERTIFIED_BY_RULE"
    assert len(result["certificate_hash"]) == 64


def test_langreth_wrong_rule_is_nonzero():
    result = verify_langreth(["A", "B"], "less", "A_R*B_less + A_less*B_R")
    assert result["status"] == "NONZERO"
    assert "A_less" not in result["residual"]  # expressed in independent R, A, K


def test_cli_manybody_emits_json(capsys):
    assert cli.main(["manybody", "langreth", "--product", "A,B", "--component", "R",
                     "--claim", "A_R*B_R"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "CERTIFIED_BY_RULE"
    assert cli.main(["manybody", "remainder", "--function", "a/g + b*g", "--approximant",
                     "a/g", "--variable", "g", "--point", "0", "--order", "1",
                     "--symbols", '[{"name": "a"}, {"name": "b"}, {"name": "g", "nonzero": true}]']) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "CERTIFIED_BY_RULE"
    assert cli.main(["manybody", "matsubara", "--statistics", "fermion", "--summand",
                     "1/(z-a)", "--claim", "nF(a)", "--symbols", "not: [valid"]) == 2
