"""Emit DEV and frozen TEST JSON for ssc-representation-bench-v0.1.

TEST files are freeze artifacts. Regenerating them is a version bump.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from research.representation_invention.bench.loader import (
    BENCH_ROOT,
    FREEZE_MANIFEST,
    TASKS_DEV,
    TASKS_TEST,
    VERSION,
    validate_task,
)

CTX = [
    "Exact source members are listed in the catalog. Cite only G#### ids.",
    "Propose a complete representation: type, members, latent object, operators, reconstruction, and checkable obligations.",
    "Do not invent aliases. Do not claim a final compact formula. Do not invent physical names.",
]
CTX_THERMAL = CTX + [
    "Thermal-style analytic object. Shared structure may exist.",
]
CTX_GREEN = CTX + [
    "Resolvent-style object. Shared poles may exist.",
]
CTX_RESPONSE = CTX + [
    "Response-style object. Shared denominators may exist.",
]
CTX_PERT = CTX + [
    "Perturbative fragment. Shared denominator structure may exist.",
]
CTX_TENSOR = CTX + [
    "Indexed tensor expression. Index permutation may expose structure.",
]
CTX_POINTER = [
    "Catalog is external and owned by a separate DEV case study.",
    "Do not load a full case-study expression from this task file.",
]


def S(*names: str) -> list[dict]:
    return [{"name": n, "real": True} for n in names]


def catalog(*texts: str) -> list[dict]:
    return [{"id": f"G{i:04d}", "text": t} for i, t in enumerate(texts, 1)]


def item(
    *,
    id: str,
    split: str,
    tier: str,
    family: str,
    current: str,
    symbols: list[dict],
    functions: list[str],
    catalog: list[dict],
    target_type: Optional[str],
    r_level: Optional[str],
    polarity: str,
    difficulty: int,
    provenance_hidden: str,
    assumptions: Optional[list[str]] = None,
    scientific_context: Optional[list[str]] = None,
    instance_maps: Optional[dict] = None,
    negative_tempting_structures: Optional[list[str]] = None,
    notes: str = "",
    expected_verdict: Optional[str] = None,
    domain: str = "synthetic",
    catalog_external: bool = False,
    hidden_gold: Optional[dict] = None,
    source_expressions: Optional[list[str]] = None,
) -> dict:
    texts = [e["text"] for e in catalog]
    src = list(source_expressions) if source_expressions is not None else []
    if source_expressions is None:
        if current:
            src.append(current)
        for t in texts:
            if t not in src:
                src.append(t)
    gold_types = [target_type] if target_type else []
    imap = dict(instance_maps or {})
    rec: dict[str, Any] = {
        "id": id,
        "version": VERSION,
        "split": split,
        "tier": tier,
        "family": family,
        "domain": domain,
        "task": "representation_invention",
        "current": current,
        "source_expressions": src,
        "symbols": symbols,
        "functions": functions,
        "assumptions": list(assumptions or []),
        "catalog": catalog,
        "source_format": "sympy",
        "scientific_context": list(scientific_context or CTX),
        "license": "author-constructed",
        "hidden_from_proposer": True,
        "target_type": target_type,
        "hidden_target_type": target_type,
        "gold_types": gold_types,
        "instance_maps": imap,
        "hidden_instance_maps": dict(imap),
        "r_level": r_level,
        "hidden_r_level": r_level,
        "ladder_id": r_level,
        "polarity": polarity,
        "negative_tempting_structures": list(negative_tempting_structures or []),
        "provenance_hidden": provenance_hidden,
        "difficulty": difficulty,
        "expected_verdict": expected_verdict
        if expected_verdict is not None
        else ("NONZERO" if polarity == "negative" else "ZERO"),
        "notes": notes,
        "hidden_gold": hidden_gold or {"aux_names": []},
    }
    if catalog_external:
        rec["catalog_external"] = True
        rec["expected_verdict"] = None
    validate_task(rec, expected_split=split)
    return rec


def all_items() -> list[dict]:
    items: list[dict] = []

    # ----- Tier A DEV: clean math controls -----
    items.append(item(
        id="dev-a-newton-first", split="dev", tier="A", family="newton_first",
        current="(f(x) - f(y))/(x - y)",
        symbols=S("x", "y"), functions=["f"],
        catalog=catalog("(f(x) - f(y))/(x - y)", "f(x)", "f(y)"),
        assumptions=["Ne(x, y)"],
        target_type="divided_difference", r_level="R1", polarity="positive",
        difficulty=1,
        instance_maps={
            "G0001": {"nodes": ["x", "y"], "latent": "f"},
        },
        hidden_gold={"aux_names": ["DDf"]},
        provenance_hidden="Newton first divided difference control",
        notes="F[x,y] = (F(x)-F(y))/(x-y)",
    ))
    items.append(item(
        id="dev-a-repeated-node", split="dev", tier="A", family="repeated_node",
        current="df(x)",
        symbols=S("x", "y"), functions=["f", "df"],
        catalog=catalog("(f(x) - f(y))/(x - y)", "df(x)"),
        assumptions=["df is the x-derivative of f"],
        target_type="hermite_divided_difference", r_level="R2",
        polarity="positive", difficulty=2,
        instance_maps={
            "G0001": {"nodes": ["x", "y"], "multiplicities": [1, 1]},
            "G0002": {"nodes": ["x", "x"], "multiplicities": [2]},
        },
        hidden_gold={"aux_names": ["Fxx"]},
        provenance_hidden="Repeated-node identity F[x,x] = F'(x)",
        notes="diagonal of first DD",
    ))
    items.append(item(
        id="dev-a-hermite-two", split="dev", tier="A", family="hermite_two",
        current="(df(x) - (f(x) - f(y))/(x - y))/(x - y)",
        symbols=S("x", "y"), functions=["f", "df"],
        catalog=catalog(
            "(f(x) - f(y))/(x - y)",
            "df(x)",
            "(df(x) - (f(x) - f(y))/(x - y))/(x - y)",
        ),
        assumptions=["Ne(x, y)", "df is the x-derivative of f"],
        target_type="hermite_divided_difference", r_level="R3",
        polarity="positive", difficulty=3,
        instance_maps={
            "G0003": {"nodes": ["x", "x", "y"], "multiplicities": [2, 1]},
        },
        hidden_gold={"aux_names": ["FxxY"]},
        provenance_hidden="Hermite DD F[x,x,y] from first DD and derivative",
        notes="(F[x,x]-F[x,y])/(x-y)",
    ))
    items.append(item(
        id="dev-a-deriv-family", split="dev", tier="A", family="deriv",
        current="polygamma(0, z) + polygamma(1, z)",
        symbols=S("z"), functions=[],
        catalog=catalog("polygamma(0, z)", "polygamma(1, z)"),
        target_type="derivative_family", r_level="R6", polarity="positive",
        difficulty=2,
        instance_maps={
            "G0001": {"order": 0},
            "G0002": {"order": 1, "operator": "d/dz"},
        },
        hidden_gold={"aux_names": ["PsiFam"]},
        provenance_hidden="polygamma derivative family",
        notes="polygamma(1,z) = d/dz polygamma(0,z)",
    ))
    items.append(item(
        id="dev-a-recurrence-family", split="dev", tier="A", family="recurrence",
        current="T(n + 1, x) - 2*x*T(n, x) + T(n - 1, x)",
        symbols=S("n", "x"), functions=["T"],
        catalog=catalog("T(n + 1, x)", "T(n, x)", "T(n - 1, x)"),
        target_type="recurrence_family", r_level="R6", polarity="positive",
        difficulty=2,
        instance_maps={
            "G0001": {"shift": 1},
            "G0002": {"shift": 0},
            "G0003": {"shift": -1},
        },
        hidden_gold={"aux_names": ["Trec"]},
        provenance_hidden="three-term recurrence family",
        notes="T(n+1,x) = 2x T(n,x) - T(n-1,x)",
    ))
    items.append(item(
        id="dev-a-wrong-sign-dd", split="dev", tier="A", family="wrong_sign",
        current="(f(x) + f(y))/(x - y)",
        symbols=S("x", "y"), functions=["f"],
        catalog=catalog("(f(x) + f(y))/(x - y)", "f(x)", "f(y)"),
        assumptions=["Ne(x, y)"],
        target_type=None, r_level=None, polarity="negative", difficulty=2,
        negative_tempting_structures=["divided_difference"],
        provenance_hidden="wrong-sign / sum numerator is not Newton first DD",
        notes="(F(x)+F(y))/(x-y) is not F[x,y]",
        expected_verdict="NONZERO",
    ))

    # ----- Tier B DEV: representation change -----
    items.append(item(
        id="dev-b-piecewise-dd", split="dev", tier="B", family="piecewise_unify",
        current="Piecewise(((f(x) - f(y))/(x - y), Ne(x, y)), (df(x), True))",
        symbols=S("x", "y"), functions=["f", "df"],
        catalog=catalog("(f(x) - f(y))/(x - y)", "df(x)"),
        assumptions=["df is the x-derivative of f"],
        target_type="divided_difference", r_level="R4", polarity="positive",
        difficulty=3,
        instance_maps={
            "G0001": {"nodes": ["x", "y"], "role": "generic"},
            "G0002": {"nodes": ["x", "x"], "role": "degenerate"},
        },
        hidden_gold={"aux_names": ["PwDD"]},
        provenance_hidden="Piecewise branches of one DD family",
        notes="generic first DD and repeated-node branch",
    ))
    items.append(item(
        id="dev-b-branch-degen", split="dev", tier="B", family="branch_degen",
        current="Piecewise((K(n, m), Ne(n, m)), (K(n, n), True))",
        symbols=S("n", "m"), functions=["K"],
        catalog=catalog("K(n, m)", "K(n, n)"),
        target_type="local_confluence", r_level="R0", polarity="positive",
        difficulty=2,
        instance_maps={
            "G0001": {"role": "generic"},
            "G0002": {"role": "degenerate", "limit": "m -> n"},
        },
        hidden_gold={"aux_names": ["Kfam"]},
        provenance_hidden="degenerate branch is a specialization of the generic",
        notes="limit m->n of K(n,m) is K(n,n)",
    ))
    items.append(item(
        id="dev-b-special-fn", split="dev", tier="B", family="special_fn",
        current="(polygamma(0, x) - polygamma(0, y))/(x - y)",
        symbols=S("x", "y"), functions=[],
        catalog=catalog(
            "(polygamma(0, x) - polygamma(0, y))/(x - y)",
            "polygamma(0, x)",
            "polygamma(0, y)",
        ),
        assumptions=["Ne(x, y)"],
        target_type="divided_difference", r_level="R5", polarity="positive",
        difficulty=3,
        instance_maps={
            "G0001": {"nodes": ["x", "y"], "latent": "polygamma(0, z)"},
        },
        hidden_gold={"aux_names": ["PsiDD"]},
        provenance_hidden="special-function Newton first DD",
        notes="F = polygamma(0, ·)",
    ))
    items.append(item(
        id="dev-b-master-induct", split="dev", tier="B", family="induction",
        current="G(a) + G(b) + G(c)",
        symbols=S("a", "b", "c"), functions=["G"],
        catalog=catalog("G(a)", "G(b)", "G(c)"),
        target_type="master_function", r_level="R6", polarity="positive",
        difficulty=2,
        instance_maps={
            "G0001": {"theta": "a"},
            "G0002": {"theta": "b"},
            "G0003": {"theta": "c"},
        },
        hidden_gold={"aux_names": ["Gmast"]},
        provenance_hidden="three specializations of one master object",
        notes="nontrivial instance maps, not F := A1",
    ))
    items.append(item(
        id="dev-b-nonconfluent-pw", split="dev", tier="B", family="nonconfluent",
        current="Piecewise((K(n, m), Ne(n, m)), (L(n, n), True))",
        symbols=S("n", "m"), functions=["K", "L"],
        catalog=catalog("K(n, m)", "L(n, n)"),
        target_type=None, r_level=None, polarity="negative", difficulty=2,
        negative_tempting_structures=["local_confluence", "divided_difference"],
        provenance_hidden="distinct heads; branches are not one confluent family",
        notes="K and L are independent",
        expected_verdict="NONZERO",
    ))
    items.append(item(
        id="dev-b-tautological-master", split="dev", tier="B", family="tautology",
        current="A(x)",
        symbols=S("x"), functions=["A"],
        catalog=catalog("A(x)"),
        target_type=None, r_level=None, polarity="negative", difficulty=1,
        negative_tempting_structures=["master_function"],
        instance_maps={"G0001": {"bait": "F := G0001"}},
        provenance_hidden="tautological master bait F := A1 used once",
        notes="a single member is not a master object",
        expected_verdict="NONZERO",
    ))

    # ----- Tier C DEV: scientific-flavored, not full Guo -----
    items.append(item(
        id="dev-c-thermal-kernel", split="dev", tier="C", family="thermal",
        domain="thermal",
        current="A*polygamma(0, zP) + A*polygamma(0, zM)",
        symbols=S("A", "zP", "zM"), functions=[],
        catalog=catalog("polygamma(0, zP)", "polygamma(0, zM)"),
        scientific_context=CTX_THERMAL,
        target_type="master_function", r_level="R6", polarity="positive",
        difficulty=3,
        instance_maps={
            "G0001": {"z": "zP"},
            "G0002": {"z": "zM"},
        },
        hidden_gold={"aux_names": ["PsiTh"]},
        provenance_hidden="thermal-kernel-like polygamma pair",
        notes="shared polygamma(0, z) master",
    ))
    items.append(item(
        id="dev-c-green-like", split="dev", tier="C", family="green",
        domain="green",
        current="1/(w - e(n) + I*eta) + 1/(w - e(m) + I*eta)",
        symbols=S("w", "n", "m", "eta"), functions=["e"],
        catalog=catalog(
            "1/(w - e(n) + I*eta)",
            "1/(w - e(m) + I*eta)",
        ),
        scientific_context=CTX_GREEN,
        target_type="master_function", r_level="R6", polarity="positive",
        difficulty=3,
        instance_maps={
            "G0001": {"pole": "e(n)"},
            "G0002": {"pole": "e(m)"},
        },
        hidden_gold={"aux_names": ["Gret"]},
        provenance_hidden="Green-function-like two-pole resolvent",
        notes="shared 1/(w - e + I*eta)",
    ))
    items.append(item(
        id="dev-c-nl-response", split="dev", tier="C", family="response",
        domain="response",
        current=(
            "v(n, m)*v(m, n)/(e(n) - e(m) + I*eta)"
            " + u(n, m)*u(m, n)/(e(n) - e(m) + I*eta)"
        ),
        symbols=S("n", "m", "eta"), functions=["v", "u", "e"],
        catalog=catalog(
            "v(n, m)*v(m, n)/(e(n) - e(m) + I*eta)",
            "u(n, m)*u(m, n)/(e(n) - e(m) + I*eta)",
            "1/(e(n) - e(m) + I*eta)",
        ),
        scientific_context=CTX_RESPONSE,
        target_type="master_function", r_level="R7", polarity="positive",
        difficulty=4,
        instance_maps={
            "G0001": {"vertex": "v", "kernel": "G0003"},
            "G0002": {"vertex": "u", "kernel": "G0003"},
        },
        hidden_gold={"aux_names": ["Kresp"]},
        provenance_hidden="nonlinear-response fragment with shared denominator",
        notes="two channels, one denominator kernel",
    ))
    items.append(item(
        id="dev-c-pert-denom", split="dev", tier="C", family="pert_denom",
        domain="perturbation",
        current="V(p)/(om - e(p)) + V(q)/(om - e(q))",
        symbols=S("p", "q", "om"), functions=["V", "e"],
        catalog=catalog("V(p)/(om - e(p))", "V(q)/(om - e(q))"),
        scientific_context=CTX_PERT,
        target_type="master_function", r_level="R6", polarity="positive",
        difficulty=3,
        instance_maps={
            "G0001": {"theta": "p"},
            "G0002": {"theta": "q"},
        },
        hidden_gold={"aux_names": ["BornW"]},
        provenance_hidden="perturbative denominator specializations",
        notes="shared V(theta)/(om - e(theta))",
    ))
    items.append(item(
        id="dev-c-tensor-family", split="dev", tier="C", family="tensor",
        domain="tensor",
        current="T(i, j)*v(i)*v(j) + T(j, i)*v(j)*v(i)",
        symbols=S("i", "j"), functions=["T", "v"],
        catalog=catalog("T(i, j)*v(i)*v(j)", "T(j, i)*v(j)*v(i)"),
        scientific_context=CTX_TENSOR,
        target_type="tensor_generator", r_level="R8", polarity="positive",
        difficulty=3,
        instance_maps={
            "G0001": {"perm": [0, 1]},
            "G0002": {"perm": [1, 0]},
        },
        hidden_gold={"aux_names": ["Tgen"]},
        provenance_hidden="tensor family under index swap",
        notes="orbit of one bilinear generator",
    ))
    items.append(item(
        id="dev-guo-pointer", split="dev", tier="C", family="external_pointer",
        domain="case_study",
        current="",
        symbols=[], functions=[],
        catalog=[],
        catalog_external=True,
        scientific_context=CTX_POINTER,
        source_expressions=[],
        target_type=None, r_level=None, polarity="positive", difficulty=5,
        expected_verdict=None,
        provenance_hidden="pointer to external DEV catalog; not TEST",
        notes="case-study catalog is owned elsewhere; do not paste the full expression",
    ))

    # ----- frozen TEST (held-out symbols / expressions) -----
    items.append(item(
        id="test-a-newton-first", split="test", tier="A", family="newton_first",
        current="(s(p) - s(q))/(p - q)",
        symbols=S("p", "q"), functions=["s"],
        catalog=catalog("(s(p) - s(q))/(p - q)", "s(p)", "s(q)"),
        assumptions=["Ne(p, q)"],
        target_type="divided_difference", r_level="R1", polarity="positive",
        difficulty=1,
        instance_maps={"G0001": {"nodes": ["p", "q"], "latent": "s"}},
        hidden_gold={"aux_names": ["DDs"]},
        provenance_hidden="held-out Newton first DD",
        notes="F[p,q] for s",
    ))
    items.append(item(
        id="test-a-repeated-node", split="test", tier="A", family="repeated_node",
        current="ds(p)",
        symbols=S("p", "q"), functions=["s", "ds"],
        catalog=catalog("(s(p) - s(q))/(p - q)", "ds(p)"),
        assumptions=["ds is the p-derivative of s"],
        target_type="hermite_divided_difference", r_level="R2",
        polarity="positive", difficulty=2,
        instance_maps={
            "G0001": {"nodes": ["p", "q"]},
            "G0002": {"nodes": ["p", "p"]},
        },
        hidden_gold={"aux_names": ["Spp"]},
        provenance_hidden="held-out repeated-node DD",
        notes="F[p,p] = F'(p)",
    ))
    items.append(item(
        id="test-a-hermite-two", split="test", tier="A", family="hermite_two",
        current="(ds(p) - (s(p) - s(q))/(p - q))/(p - q)",
        symbols=S("p", "q"), functions=["s", "ds"],
        catalog=catalog(
            "(s(p) - s(q))/(p - q)",
            "ds(p)",
            "(ds(p) - (s(p) - s(q))/(p - q))/(p - q)",
        ),
        assumptions=["Ne(p, q)", "ds is the p-derivative of s"],
        target_type="hermite_divided_difference", r_level="R3",
        polarity="positive", difficulty=3,
        instance_maps={
            "G0003": {"nodes": ["p", "p", "q"], "multiplicities": [2, 1]},
        },
        hidden_gold={"aux_names": ["SppQ"]},
        provenance_hidden="held-out Hermite DD F[p,p,q]",
        notes="(F[p,p]-F[p,q])/(p-q)",
    ))
    items.append(item(
        id="test-a-deriv-family", split="test", tier="A", family="deriv",
        current="polygamma(0, u) + polygamma(1, u)",
        symbols=S("u"), functions=[],
        catalog=catalog("polygamma(0, u)", "polygamma(1, u)"),
        target_type="derivative_family", r_level="R6", polarity="positive",
        difficulty=2,
        instance_maps={"G0001": {"order": 0}, "G0002": {"order": 1}},
        hidden_gold={"aux_names": ["PsiU"]},
        provenance_hidden="held-out polygamma derivative family",
        notes="order 0 and 1",
    ))
    items.append(item(
        id="test-a-recurrence-family", split="test", tier="A", family="recurrence",
        current="U(k + 1, z) - 2*z*U(k, z) + U(k - 1, z)",
        symbols=S("k", "z"), functions=["U"],
        catalog=catalog("U(k + 1, z)", "U(k, z)", "U(k - 1, z)"),
        target_type="recurrence_family", r_level="R6", polarity="positive",
        difficulty=2,
        instance_maps={
            "G0001": {"shift": 1},
            "G0002": {"shift": 0},
            "G0003": {"shift": -1},
        },
        hidden_gold={"aux_names": ["Urec"]},
        provenance_hidden="held-out three-term recurrence",
        notes="Chebyshev-like shift family",
    ))
    items.append(item(
        id="test-a-wrong-sign-dd", split="test", tier="A", family="wrong_sign",
        current="(s(p) + s(q))/(p - q)",
        symbols=S("p", "q"), functions=["s"],
        catalog=catalog("(s(p) + s(q))/(p - q)", "s(p)", "s(q)"),
        assumptions=["Ne(p, q)"],
        target_type=None, r_level=None, polarity="negative", difficulty=2,
        negative_tempting_structures=["divided_difference"],
        provenance_hidden="held-out wrong-sign DD bait",
        notes="sum numerator is not Newton first DD",
        expected_verdict="NONZERO",
    ))
    items.append(item(
        id="test-b-piecewise-dd", split="test", tier="B", family="piecewise_unify",
        current="Piecewise(((s(p) - s(q))/(p - q), Ne(p, q)), (ds(p), True))",
        symbols=S("p", "q"), functions=["s", "ds"],
        catalog=catalog("(s(p) - s(q))/(p - q)", "ds(p)"),
        assumptions=["ds is the p-derivative of s"],
        target_type="divided_difference", r_level="R4", polarity="positive",
        difficulty=3,
        instance_maps={
            "G0001": {"nodes": ["p", "q"]},
            "G0002": {"nodes": ["p", "p"]},
        },
        hidden_gold={"aux_names": ["PwS"]},
        provenance_hidden="held-out piecewise-to-DD unification",
        notes="generic and repeated-node branches",
    ))
    items.append(item(
        id="test-b-special-fn", split="test", tier="B", family="special_fn",
        current="(exp(a) - exp(b))/(a - b)",
        symbols=S("a", "b"), functions=[],
        catalog=catalog("(exp(a) - exp(b))/(a - b)", "exp(a)", "exp(b)"),
        assumptions=["Ne(a, b)"],
        target_type="divided_difference", r_level="R5", polarity="positive",
        difficulty=3,
        instance_maps={"G0001": {"nodes": ["a", "b"], "latent": "exp"}},
        hidden_gold={"aux_names": ["ExpDD"]},
        provenance_hidden="held-out special-function DD using exp",
        notes="F = exp",
    ))
    items.append(item(
        id="test-b-nonconfluent-pw", split="test", tier="B", family="nonconfluent",
        current="Piecewise((Q(x, y), Ne(x, y)), (R(x, x), True))",
        symbols=S("x", "y"), functions=["Q", "R"],
        catalog=catalog("Q(x, y)", "R(x, x)"),
        target_type=None, r_level=None, polarity="negative", difficulty=2,
        negative_tempting_structures=["local_confluence", "divided_difference"],
        provenance_hidden="held-out non-confluent piecewise",
        notes="Q and R are independent",
        expected_verdict="NONZERO",
    ))
    items.append(item(
        id="test-b-tautological-master", split="test", tier="B", family="tautology",
        current="H(u)",
        symbols=S("u"), functions=["H"],
        catalog=catalog("H(u)"),
        target_type=None, r_level=None, polarity="negative", difficulty=1,
        negative_tempting_structures=["master_function"],
        instance_maps={"G0001": {"bait": "F := G0001"}},
        provenance_hidden="held-out tautological master bait",
        notes="single member is not a master object",
        expected_verdict="NONZERO",
    ))
    items.append(item(
        id="test-c-thermal-kernel", split="test", tier="C", family="thermal",
        domain="thermal",
        current="B*polygamma(0, zp) + B*polygamma(0, zm)",
        symbols=S("B", "zp", "zm"), functions=[],
        catalog=catalog("polygamma(0, zp)", "polygamma(0, zm)"),
        scientific_context=CTX_THERMAL,
        target_type="master_function", r_level="R6", polarity="positive",
        difficulty=3,
        instance_maps={"G0001": {"z": "zp"}, "G0002": {"z": "zm"}},
        hidden_gold={"aux_names": ["PsiB"]},
        provenance_hidden="held-out thermal-kernel-like pair",
        notes="shared polygamma(0, z)",
    ))
    items.append(item(
        id="test-c-green-like", split="test", tier="C", family="green",
        domain="green",
        current="1/(nu - xi(1) + I*eta) + 1/(nu - xi(2) + I*eta)",
        symbols=S("nu", "eta"), functions=["xi"],
        catalog=catalog(
            "1/(nu - xi(1) + I*eta)",
            "1/(nu - xi(2) + I*eta)",
        ),
        scientific_context=CTX_GREEN,
        target_type="master_function", r_level="R6", polarity="positive",
        difficulty=3,
        instance_maps={"G0001": {"pole": "xi(1)"}, "G0002": {"pole": "xi(2)"}},
        hidden_gold={"aux_names": ["Gtwo"]},
        provenance_hidden="held-out Green-function-like resolvent pair",
        notes="shared 1/(nu - xi + I*eta)",
    ))
    items.append(item(
        id="test-c-nl-response", split="test", tier="C", family="response",
        domain="response",
        current=(
            "jx(n, m)*jx(m, n)/(om - e(n) + e(m) + I*eta)"
            " + jy(n, m)*jy(m, n)/(om - e(n) + e(m) + I*eta)"
        ),
        symbols=S("n", "m", "om", "eta"), functions=["jx", "jy", "e"],
        catalog=catalog(
            "jx(n, m)*jx(m, n)/(om - e(n) + e(m) + I*eta)",
            "jy(n, m)*jy(m, n)/(om - e(n) + e(m) + I*eta)",
            "1/(om - e(n) + e(m) + I*eta)",
        ),
        scientific_context=CTX_RESPONSE,
        target_type="master_function", r_level="R7", polarity="positive",
        difficulty=4,
        instance_maps={
            "G0001": {"vertex": "jx", "kernel": "G0003"},
            "G0002": {"vertex": "jy", "kernel": "G0003"},
        },
        hidden_gold={"aux_names": ["Kxy"]},
        provenance_hidden="held-out nonlinear-response fragment",
        notes="two channels, one denominator",
    ))
    items.append(item(
        id="test-c-tensor-family", split="test", tier="C", family="tensor",
        domain="tensor",
        current="S(mu, nu)*p(mu)*p(nu) + S(nu, mu)*p(nu)*p(mu)",
        symbols=S("mu", "nu"), functions=["S", "p"],
        catalog=catalog("S(mu, nu)*p(mu)*p(nu)", "S(nu, mu)*p(nu)*p(mu)"),
        scientific_context=CTX_TENSOR,
        target_type="tensor_generator", r_level="R8", polarity="positive",
        difficulty=3,
        instance_maps={
            "G0001": {"perm": [0, 1]},
            "G0002": {"perm": [1, 0]},
        },
        hidden_gold={"aux_names": ["Sgen"]},
        provenance_hidden="held-out tensor family under index swap",
        notes="orbit of one bilinear generator",
    ))
    return items


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_tasks(root: Path = BENCH_ROOT) -> dict:
    dev_dir = root / "tasks" / "dev"
    test_dir = root / "tasks" / "test"
    man_path = root / "validation" / "freeze_manifest.json"
    dev_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    man_path.parent.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for rec in all_items():
        folder = dev_dir if rec["split"] == "dev" else test_dir
        path = folder / f"{rec['id']}.json"
        path.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
        written.append(path)

    test_files = sorted(p for p in written if p.parent.name == "test")
    manifest = {
        "version": VERSION,
        "split": "test",
        "policy": "TEST files are frozen. Do not retune against TEST.",
        "n_test": len(test_files),
        "files": {p.name: _sha256_file(p) for p in test_files},
    }
    man_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return {
        "n_dev": sum(1 for p in written if p.parent.name == "dev"),
        "n_test": len(test_files),
        "n_written": len(written),
        "freeze_manifest": str(man_path),
    }


def main() -> None:
    info = write_tasks()
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
