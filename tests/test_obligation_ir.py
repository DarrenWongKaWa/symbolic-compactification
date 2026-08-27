"""Track B obligation IR. Frozen LLM runs are read-only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.schema import LLMStructureHypothesis
from research.obligation_ir.compiler import compile_hypothesis
from research.obligation_ir.guo import g1_discovery
from research.obligation_ir.schema import COMPILE_FAILURE, COMPILE_OK, DERIVATIVE, PERMUTATION
from research.obligation_ir.verify import verify_obligation
from research.representation_search.schema import RepresentationHypothesis


def _perm():
    return LLMStructureHypothesis(
        hypothesis_type="symmetry_invariant",
        target_members=["T(i, j)", "T(j, i)"],
        latent_object="T(x, y)",
        parameters=["x", "y"],
        operators=[
            {"member": "T(i, j)", "O": "identity"},
            {"member": "T(j, i)", "O": "permute"},
        ],
        instance_maps=[
            {"member": "T(i, j)", "theta": {"x": "i", "y": "j"}},
            {"member": "T(j, i)", "theta": {"x": "i", "y": "j"}},
        ],
        construction_plan="swap",
        required_assumptions=[],
        proof_obligations=["T(i,j)-id=0", "T(j,i)-permute=0"],
        rationale="orbit",
        confidence=0.8,
    )


def test_hrepr_schema_exists():
    h = RepresentationHypothesis(
        representation_type="divided_difference",
        language_from="Piecewise",
        language_to="divided_difference",
        latent_function="F(z)",
        nodes=["x", "y"],
    )
    assert h.representation_type == "divided_difference"


def test_permute_compiles_and_zeros():
    cr = compile_hypothesis(
        _perm(),
        symbols=[{"name": "i", "real": True}, {"name": "j", "real": True}],
        functions=["T"],
    )
    assert cr.n_fail == 0, cr.to_dict()
    kinds = {o.kind for o in cr.obligations}
    assert PERMUTATION in kinds
    vs = [
        verify_obligation(
            o,
            symbols=[{"name": "i", "real": True}, {"name": "j", "real": True}],
            functions=["T"],
        )
        for o in cr.obligations
    ]
    assert all(v.verdict == "ZERO" for v in vs), [v.to_dict() for v in vs]


def test_nickname_member_is_compile_failure_not_zero():
    hyp = LLMStructureHypothesis(
        hypothesis_type="divided_difference",
        target_members=["S1_True"],
        latent_object="D[F](x,y)",
        parameters=["x", "y"],
        operators=[{"member": "S1_True", "O": "identity"}],
        instance_maps=[{"member": "S1_True", "theta": {"nodes": "epsilon(m)"}}],
        construction_plan="",
        required_assumptions=[],
        proof_obligations=["S1_True - D_2 == 0"],
        rationale="divided difference of polygamma",
        confidence=0.5,
    )
    cr = compile_hypothesis(hyp, symbols=[{"name": "x", "real": True}], functions=["F", "D"])
    assert cr.n_ok == 0
    assert cr.obligations[0].compile_status == COMPILE_FAILURE
    v = verify_obligation(cr.obligations[0], symbols=[{"name": "x", "real": True}], functions=["F"])
    assert v.verdict == "UNKNOWN"
    assert v.compile_status == COMPILE_FAILURE


def test_g1_requires_explicit_dd_type():
    vague = LLMStructureHypothesis(
        hypothesis_type="other_structured",
        target_members=["a", "b"],
        latent_object="maybe a unified object",
        parameters=[],
        operators=[],
        instance_maps=[],
        construction_plan="",
        required_assumptions=[],
        proof_obligations=[],
        rationale="maybe unified",
        confidence=0.2,
    )
    assert g1_discovery([vague])["pass"] is False
    dd = LLMStructureHypothesis(
        hypothesis_type="divided_difference",
        target_members=["S1_True"],
        latent_object="divided differences of F_+(z)=polygamma(0,z)",
        parameters=["z"],
        operators=[],
        instance_maps=[{"member": "S1_True", "theta": {"nodes": ["x", "y"]}}],
        construction_plan="",
        required_assumptions=[],
        proof_obligations=[],
        rationale="off diagonal is a DD",
        confidence=0.4,
    )
    assert g1_discovery([dd])["pass"] is True


def test_node_id_exact_bind():
    from research.obligation_ir.source_index import SourceIndex, SourceNode
    from research.obligation_ir.grounding import EXACT_BIND, bind_alias
    n = SourceNode("G0001", "sol_node", "x + y", "Add(x,y)", 1, sol_node_id="N0014")
    idx = SourceIndex([n])
    b = bind_alias("N0014", idx)
    assert b.confidence == EXACT_BIND
    assert b.text == "x + y"


def test_h_factor_unique_bind_and_no_guess_s1():
    from research.obligation_ir.source_index import build_index
    from research.obligation_ir.grounding import (
        EXACT_BIND, UNIQUE_STRUCTURAL_BIND, NO_BIND, AMBIGUOUS_BIND,
        bind_alias,
    )
    expr = (
        "Sum(Piecewise((a(n), Eq(m, n)), (f(m), True)), (n, 1, N), (m, 1, N))"
        " + Sum(Piecewise((b(n), Eq(m, n)), (g(m), True)), (n, 1, N), (m, 1, N))"
    )
    idx = build_index(
        expr,
        [{"name": x, "real": True} for x in "nmN"],
        ["a", "b", "f", "g"],
    )
    b = bind_alias("S1_True", idx, theta={"collision": "generic"}, latent="")
    assert b.confidence in {AMBIGUOUS_BIND, NO_BIND}, b
    expr2 = (
        "Sum(Piecewise((K(n), Eq(m, n)), (G(m, n)*h1(b, n, m)*h2(a, c, m, n), True)), (n, 1, N), (m, 1, N))"
        "+ Sum(Piecewise((K(n), Eq(m, n)), (G(m, n)*h1(c, n, m)*h2(a, b, m, n), True)), (n, 1, N), (m, 1, N))"
    )
    idx2 = build_index(
        expr2,
        [{"name": x, "real": True} for x in "nmNabc"],
        ["K", "G", "h1", "h2"],
    )
    b2 = bind_alias(
        "S1_True", idx2,
        theta={"h_factor": "h1(b, n, m)*h2(a, c, m, n)", "collision": "True"},
        latent="",
        functions=["K", "G", "h1", "h2"],
    )
    assert b2.confidence == UNIQUE_STRUCTURAL_BIND, b2
    assert b2.kind == "piecewise_branch"
    b3 = bind_alias("S1", idx2, theta={}, latent="no h calls here")
    assert b3.confidence == NO_BIND, b3


def test_newton_dd_compile_on_toy():
    from research.obligation_ir.source_index import build_index
    from research.obligation_ir.grounding import bind_hypothesis_members, UNIQUE_STRUCTURAL_BIND
    from research.obligation_ir.repr_compile import compile_dd
    expr = (
        "Sum(Piecewise((polygamma(0, n), Eq(m, n)), "
        "((polygamma(0, m)-polygamma(0, n))/(m-n), True)), (n, 1, N), (m, 1, N))"
    )
    idx = build_index(expr, [{"name": x, "real": True} for x in "nmN"], [])
    hyp = {
        "hypothesis_type": "divided_difference",
        "latent_object": "F_+(z)=polygamma(0,z)",
        "target_members": ["S_True"],
        "instance_maps": [{
            "member": "S_True",
            "theta": {"collision": "True", "nodes": ["m", "n"]},
        }],
    }
    binds = bind_hypothesis_members(
        hyp, idx,
        symbols=[{"name": x, "real": True} for x in "nmN"],
        functions=[],
    )
    assert any(b.admissible for b in binds), binds
    rows = compile_dd(
        hyp, binds, idx,
        symbols=[{"name": x, "real": True} for x in "nmN"],
        functions=[],
    )
    # F_+(z)=f(z) extract; generic vs (f(m)-f(n))/(m-n)
    assert rows, "expected a DD obligation"
    assert any(v.verdict == "ZERO" for _, v in rows), [(o.to_dict(), v.to_dict()) for o, v in rows]


def test_frozen_run_files_not_required_to_exist_for_unit():
    p = ROOT / "research" / "llm_abstraction" / "runs" / "dev" / "T7-pos-swap__A0__deepseek-v4-pro__s0.json"
    if not p.is_file():
        return
    before = p.read_bytes()
    from research.obligation_ir.compiler import compile_hypothesis
    d = json.loads(before)
    h = d["hypotheses"][0]
    hyp = LLMStructureHypothesis(
        hypothesis_type=h["hypothesis_type"],
        target_members=h["target_members"],
        latent_object=h["latent_object"],
        parameters=h.get("parameters") or [],
        operators=h.get("operators") or [],
        instance_maps=h.get("instance_maps") or [],
        construction_plan=h.get("construction_plan") or "",
        required_assumptions=h.get("required_assumptions") or [],
        proof_obligations=h.get("proof_obligations") or [],
        rationale=h.get("rationale") or "",
        confidence=float(h.get("confidence") or 0),
    )
    compile_hypothesis(hyp, symbols=[{"name": "i", "real": True}, {"name": "j", "real": True}], functions=["T"])
    assert p.read_bytes() == before
