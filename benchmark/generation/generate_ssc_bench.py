#!/usr/bin/env python3
"""Generate ssc-bench-v0.1 and freeze hashes.

Run from repo root:
    .venv/bin/python benchmark/generation/generate_ssc_bench.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from symbolic_compactification import NONZERO, UNKNOWN, ZERO, structure_summary, verify_equivalent  # noqa: E402
from symbolic_compactification.models import AdapterError  # noqa: E402
from symbolic_compactification.parser import parse_expression  # noqa: E402

VERSION = "ssc-bench-v0.1"
SPLIT_SALT = f"{VERSION}:split"


def _sym(*names, real=True, nonzero=False):
    return [{"name": n, "real": real, "nonzero": nonzero} for n in names]


def _split(item_id: str) -> str:
    h = int(hashlib.sha256(f"{SPLIT_SALT}:{item_id}".encode()).hexdigest()[:8], 16)
    return "test" if (h % 10) < 3 else "dev"


def _descriptors(text, symbols, functions):
    try:
        expr = parse_expression(text, symbols, functions=functions or None)
        return structure_summary(expr)
    except AdapterError as exc:
        return {"error": exc.code}


def _verify(current, candidate, symbols, functions=None):
    return verify_equivalent(
        current, candidate, symbols, functions=functions or None)


def make_item(**kwargs):
    item = {
        "version": VERSION,
        "candidate": None,
        "functions": [],
        "source_format": "sympy",
        "source_file": None,
        "expected_verdict": None,
        "mutation_type": None,
        "difficulty": 1,
        "ladder_id": None,
        "hidden_from_proposer": True,
        "human_reference": None,
        "target_compact": None,
        "notes": "",
    }
    item.update(kwargs)
    item["split"] = kwargs.get("split") or _split(item["id"])
    item["structural_descriptors"] = _descriptors(
        item["current"], item["symbols"], item["functions"])
    item["hidden_from_proposer"] = True
    return item


# --------------------------------------------------------------------------- #
# Tier A seeds: identities (current, compact-or-equal candidate)
# --------------------------------------------------------------------------- #

IDENTITIES: list[dict] = [
    dict(id="A-poly-binom", family="polynomial",
         current="(x + 1)**2", candidate="x**2 + 2*x + 1",
         symbols=_sym("x"), difficulty=1),
    dict(id="A-poly-diffsq", family="polynomial",
         current="(x - 1)*(x + 1)", candidate="x**2 - 1",
         symbols=_sym("x"), difficulty=1),
    dict(id="A-poly-cube", family="polynomial",
         current="(x + y)**2", candidate="x**2 + 2*x*y + y**2",
         symbols=_sym("x", "y"), difficulty=1),
    dict(id="A-poly-cubic-exp", family="polynomial",
         current="(a + b)**3",
         candidate="a**3 + 3*a**2*b + 3*a*b**2 + b**3",
         symbols=_sym("a", "b"), difficulty=2),
    dict(id="A-poly-factor-cubic", family="polynomial",
         current="x**3 - 1", candidate="(x - 1)*(x**2 + x + 1)",
         symbols=_sym("x"), difficulty=2),
    dict(id="A-rat-partial", family="rational",
         current="1/x + 1/y", candidate="(x + y)/(x*y)",
         symbols=_sym("x", "y", nonzero=True), difficulty=2),
    dict(id="A-rat-cancel", family="rational",
         current="(x**2 + 2*x + 1)/(x + 1)", candidate="x + 1",
         symbols=_sym("x"), difficulty=2),
    dict(id="A-rat-diffsq", family="rational",
         current="(x**2 - 1)/(x - 1)", candidate="x + 1",
         symbols=_sym("x"), difficulty=2),
    dict(id="A-trig-pythag", family="trigonometric",
         current="sin(x)**2 + cos(x)**2", candidate="1",
         symbols=_sym("x"), difficulty=1),
    dict(id="A-trig-double", family="trigonometric",
         current="sin(2*x)", candidate="2*sin(x)*cos(x)",
         symbols=_sym("x"), difficulty=2),
    dict(id="A-trig-cos2", family="trigonometric",
         current="cos(2*x)", candidate="cos(x)**2 - sin(x)**2",
         symbols=_sym("x"), difficulty=2),
    dict(id="A-trig-one-minus", family="trigonometric",
         current="1 - sin(x)**2", candidate="cos(x)**2",
         symbols=_sym("x"), difficulty=1),
    dict(id="A-exp-add", family="exponential",
         current="exp(x)*exp(y)", candidate="exp(x + y)",
         symbols=_sym("x", "y"), difficulty=1),
    dict(id="A-exp-cancel", family="exponential",
         current="exp(x + y)/exp(y)", candidate="exp(x)",
         symbols=_sym("x", "y"), difficulty=2),
    dict(id="A-sum-double", family="nested_sum",
         current="Sum(f(n), (n, 1, N)) + Sum(f(n), (n, 1, N))",
         candidate="2*Sum(f(n), (n, 1, N))",
         symbols=_sym("N", "n"), functions=["f"], difficulty=2),
    dict(id="A-sum-linear", family="nested_sum",
         current="Sum(a*f(n), (n, 1, N))",
         candidate="a*Sum(f(n), (n, 1, N))",
         symbols=_sym("a", "N", "n"), functions=["f"], difficulty=2),
    dict(id="A-sum-add-bodies", family="nested_sum",
         current="Sum(f(n), (n, 1, N)) + Sum(g(n), (n, 1, N))",
         candidate="Sum(f(n) + g(n), (n, 1, N))",
         symbols=_sym("N", "n"), functions=["f", "g"], difficulty=2),
    dict(id="A-prod-const", family="product",
         current="Product(a, (n, 1, N))",
         candidate="a**N",
         symbols=_sym("a", "n", "N"), difficulty=2),
    dict(id="A-pw-abs", family="piecewise",
         current="Piecewise((x, x >= 0), (-x, True))",
         candidate="Abs(x)",
         symbols=_sym("x"), difficulty=2),
    dict(id="A-pw-same", family="piecewise",
         current="Piecewise((x + y, True))",
         candidate="x + y",
         symbols=_sym("x", "y"), difficulty=1),
    dict(id="A-cx-re", family="complex",
         current="2*re(a*conjugate(b))",
         candidate="a*conjugate(b) + conjugate(a)*b",
         symbols=_sym("a", "b", real=False), difficulty=3),
    dict(id="A-cx-polar", family="complex",
         current="Abs(a + b)**2 - Abs(a - b)**2",
         candidate="2*(a*conjugate(b) + conjugate(a)*b)",
         symbols=_sym("a", "b", real=False), difficulty=3),
    dict(id="A-sf-poly-zero", family="special_function",
         current="polygamma(0, z) - polygamma(0, z)",
         candidate="0",
         symbols=_sym("z"), difficulty=1),
    dict(id="A-sf-poly-id", family="special_function",
         current="polygamma(1, z + 1)",
         candidate="polygamma(1, z + 1)",
         symbols=_sym("z"), difficulty=1),
    dict(id="A-assume-sqrt-pos", family="assumptions",
         current="sqrt(x**2)",
         candidate="x",
         symbols=[{"name": "x", "real": True, "nonzero": True}],
         difficulty=3,
         notes="may be UNKNOWN without positivity; keep actual verdict"),
]


def mutate(identity: dict) -> list[dict]:
    cur, cand = identity["current"], identity["candidate"]
    symbols, functions = identity["symbols"], identity.get("functions", [])
    family = identity["family"]
    base = identity["id"]
    out = []

    def add(suffix, mutation, new_cand, expected=NONZERO):
        out.append(dict(
            id=f"{base}-{suffix}", family=family,
            current=cur, candidate=new_cand, symbols=symbols,
            functions=functions, mutation_type=mutation,
            expected_verdict=expected, difficulty=identity.get("difficulty", 1),
        ))

    add("wrong-sign", "wrong_sign", f"-({cand})")
    add("wrong-coeff", "wrong_coefficient", f"2*({cand})")
    add("missing-term", "missing_term", f"({cand}) + 1")
    if "/" in cand or "/" in cur:
        add("den-power", "denominator_power", f"({cand})/(x+2)" if any(
            s["name"] == "x" for s in symbols) else f"({cand})/2")
    if "Sum(" in cur:
        add("bound", "changed_summation_bound",
            cand.replace("(n, 1, N)", "(n, 1, N - 1)")
            if "(n, 1, N)" in cand else cand.replace("N", "(N + 1)"))
    if "Piecewise(" in cur:
        add("branch", "changed_branch",
            "Piecewise((-x, x >= 0), (x, True))" if "Abs" in cand or "x >= 0" in cur
            else f"Piecewise((0, True))")
    return out


UNKNOWN_SEEDS = [
    dict(id="A-unk-explog", family="assumptions",
         current="exp(log(x))", candidate="x",
         symbols=_sym("x"), difficulty=3,
         expected_verdict=UNKNOWN,
         notes="without x>0, engine should not silently promote"),
    dict(id="A-unk-gamma-not-whitelisted", family="special_function",
         current="sin(x)/x", candidate="1",
         symbols=_sym("x"), difficulty=2,
         expected_verdict=NONZERO,
         notes="sinc identity at a point is not an identity"),
    dict(id="A-unk-polygamma-reflection", family="special_function",
         current="polygamma(0, z) - polygamma(0, 1 - z)",
         candidate="pi / tan(pi*z)",
         symbols=_sym("z"), difficulty=4,
         expected_verdict=UNKNOWN,
         notes="reflection identity; engine may UNKNOWN (do not relabel)"),
    dict(id="A-assume-sqrt-not-id", family="assumptions",
         current="sqrt(x**2)", candidate="x",
         symbols=[{"name": "x", "real": True, "nonzero": True}],
         difficulty=3,
         expected_verdict=NONZERO,
         notes="sqrt(x**2)=x is false for x<0; nonzero is not positivity"),
]


# --------------------------------------------------------------------------- #
# Tier B: compactification (hidden target)
# --------------------------------------------------------------------------- #

TIER_B = [
    dict(id="B-factor-quad", family="factoring",
         current="x**2 + 5*x + 6", target_compact="(x + 2)*(x + 3)",
         symbols=_sym("x"), difficulty=1),
    dict(id="B-factor-diffsq", family="factoring",
         current="x**2 - 2*x*y + y**2", target_compact="(x - y)**2",
         symbols=_sym("x", "y"), difficulty=1),
    dict(id="B-common-kernel", family="common_kernel",
         current="a*f(n) + a*g(n)", target_compact="a*(f(n) + g(n))",
         symbols=_sym("a", "n"), functions=["f", "g"], difficulty=1),
    dict(id="B-sum-merge", family="nested_sum",
         current="Sum(f(n), (n, 1, N)) + Sum(f(n), (n, 1, N))",
         target_compact="2*Sum(f(n), (n, 1, N))",
         symbols=_sym("N", "n"), functions=["f"], difficulty=2),
    dict(id="B-sum-merge-three", family="nested_sum",
         current="Sum(f(n), (n, 1, N)) + Sum(f(n), (n, 1, N)) + Sum(f(n), (n, 1, N))",
         target_compact="3*Sum(f(n), (n, 1, N))",
         symbols=_sym("N", "n"), functions=["f"], difficulty=2),
    dict(id="B-sum-common-factor", family="common_kernel",
         current="Sum(c*h(n, m), (n, 1, N), (m, 1, N)) + Sum(c*k(n, m), (n, 1, N), (m, 1, N))",
         target_compact="c*Sum(h(n, m) + k(n, m), (n, 1, N), (m, 1, N))",
         symbols=_sym("c", "n", "m", "N"), functions=["h", "k"], difficulty=3),
    dict(id="B-together", family="rational",
         current="1/(x+1) + 1/(x-1)", target_compact="(2*x)/((x+1)*(x-1))",
         symbols=_sym("x"), difficulty=2),
    dict(id="B-cancel", family="rational",
         current="(x**3 - x)/(x**2 - 1)", target_compact="x",
         symbols=_sym("x"), difficulty=2),
    dict(id="B-trig-compact", family="trigonometric",
         current="sin(x)**2 + cos(x)**2 + sin(x)**2 + cos(x)**2",
         target_compact="2",
         symbols=_sym("x"), difficulty=2),
    dict(id="B-indexed-swap", family="indexed",
         current="h1(n, m) + h1(n, m)", target_compact="2*h1(n, m)",
         symbols=_sym("n", "m"), functions=["h1"], difficulty=1),
    dict(id="B-pw-confluent-easy", family="piecewise",
         current="Piecewise((x, True)) + Piecewise((x, True))",
         target_compact="2*x",
         symbols=_sym("x"), difficulty=2),
    dict(id="B-collect", family="factoring",
         current="x*y + x*z + x", target_compact="x*(y + z + 1)",
         symbols=_sym("x", "y", "z"), difficulty=1),
    dict(id="B-nested-sum-index", family="nested_sum",
         current="Sum(Sum(f(n, m), (m, 1, N)), (n, 1, N)) + Sum(Sum(f(n, m), (m, 1, N)), (n, 1, N))",
         target_compact="2*Sum(Sum(f(n, m), (m, 1, N)), (n, 1, N))",
         symbols=_sym("n", "m", "N"), functions=["f"], difficulty=3),
    dict(id="B-exp-kernel", family="exponential",
         current="exp(x)*exp(x)*exp(y)", target_compact="exp(2*x + y)",
         symbols=_sym("x", "y"), difficulty=2),
    dict(id="B-sym-reduce", family="symmetry",
         current="h1(n, m)*h2(m, n) + h1(n, m)*h2(m, n)",
         target_compact="2*h1(n, m)*h2(m, n)",
         symbols=_sym("n", "m"), functions=["h1", "h2"], difficulty=2),
]


# --------------------------------------------------------------------------- #
# Tier C: author-constructed scientific expressions (not paper dumps)
# Guo flagship is CONTAMINATED (used in engine experiments) -> split=dev
# --------------------------------------------------------------------------- #

TIER_C = [
    dict(
        id="C-guo-sigma-abc",
        family="kubo_response",
        current=None,  # filled from file
        source_file="examples/long/Guo_Sigma_abc_dc_exact.txt",
        source_format="wolfram",
        symbols=[
            {"name": n, "real": True, "nonzero": False}
            for n in ["Nb", "a", "b", "c", "beta", "gamma", "mu", "n", "m", "ell"]
        ],
        functions=["h1", "h2", "epsilon"],
        difficulty=5,
        split="dev",
        ladder_id="guo_sigma_abc_L0_L7",
        notes="CONTAMINATED flagship: used in 2026-08-21 skill-vs-blank. "
              "Case study only, not an unseen test item. Hidden PRB form is "
              "NOT stored in this repository.",
        provenance="examples/long/SOURCE.md SHA-256 "
                    "63742cc4e6bf401dd48e258ecb86676b0d7570cc075cae38b91dc188652afc44",
    ),
    dict(
        id="C-kubo-double-sum",
        family="kubo_response",
        current=(
            "Sum(v(n, m)*v(m, n)/(epsilon(n) - epsilon(m) + I*gamma), "
            "(n, 1, Nb), (m, 1, Nb)) + "
            "Sum(v(n, m)*v(m, n)/(epsilon(n) - epsilon(m) + I*gamma), "
            "(n, 1, Nb), (m, 1, Nb))"
        ),
        target_compact=(
            "2*Sum(v(n, m)*v(m, n)/(epsilon(n) - epsilon(m) + I*gamma), "
            "(n, 1, Nb), (m, 1, Nb))"
        ),
        symbols=_sym("n", "m", "Nb", "gamma"),
        functions=["v", "epsilon"],
        difficulty=3,
        provenance="author-constructed linear-response skeleton (not a paper dump)",
        ladder_id="generic_sum_fold",
    ),
    dict(
        id="C-green-spectral",
        family="greens_functions",
        current="1/(w - epsilon(n) + I*gamma) + 1/(w - epsilon(n) + I*gamma)",
        target_compact="2/(w - epsilon(n) + I*gamma)",
        symbols=_sym("w", "n", "gamma"),
        functions=["epsilon"],
        difficulty=2,
        provenance="author-constructed retarded Green's function kernel",
        ladder_id="generic_sum_fold",
    ),
    dict(
        id="C-matsubara-pair",
        family="thermal_kernels",
        current=(
            "Sum(1/(I*wn - e(n)), (n, 1, Nb)) + Sum(1/(I*wn - e(n)), (n, 1, Nb))"
        ),
        target_compact="2*Sum(1/(I*wn - e(n)), (n, 1, Nb))",
        symbols=_sym("wn", "n", "Nb"),
        functions=["e"],
        difficulty=2,
        provenance="author-constructed Matsubara-like sum (wn is a symbol, not a dummy)",
        ladder_id="generic_sum_fold",
    ),
    dict(
        id="C-fermi-poly-piecewise",
        family="thermal_kernels",
        current=(
            "Piecewise((polygamma(0, z), Eq(n, m)), "
            "(polygamma(0, z) - polygamma(0, z + 1), True))"
        ),
        target_compact=None,
        symbols=_sym("z", "n", "m"),
        difficulty=4,
        provenance="author-constructed polygamma/Piecewise thermal skeleton",
        notes="compact target not provided; compactness-only scoring",
    ),
    dict(
        id="C-tensor-index",
        family="tensor_identities",
        current="h1(a, b)*h2(b, c) + h1(a, b)*h2(b, c)",
        target_compact="2*h1(a, b)*h2(b, c)",
        symbols=_sym("a", "b", "c"),
        functions=["h1", "h2"],
        difficulty=2,
        provenance="author-constructed indexed vertex product",
        ladder_id="generic_sum_fold",
    ),
    dict(
        id="C-perturbation-nested",
        family="perturbation_theory",
        current=(
            "Sum(g(n)*g(m)/(omega - e(n) - e(m)), (n, 1, Nb), (m, 1, Nb)) + "
            "Sum(g(n)*g(m)/(omega - e(n) - e(m)), (n, 1, Nb), (m, 1, Nb))"
        ),
        target_compact=(
            "2*Sum(g(n)*g(m)/(omega - e(n) - e(m)), (n, 1, Nb), (m, 1, Nb))"
        ),
        symbols=_sym("n", "m", "Nb", "omega"),
        functions=["g", "e"],
        difficulty=3,
        provenance="author-constructed second-order perturbation skeleton",
        ladder_id="generic_sum_fold",
    ),
    dict(
        id="C-transport-kernel",
        family="transport",
        current=(
            "Sum(v(n)*v(n)*(-polygamma(1, z(n))), (n, 1, Nb)) + "
            "Sum(v(n)*v(n)*(-polygamma(1, z(n))), (n, 1, Nb))"
        ),
        target_compact="Sum(-2*v(n)**2*polygamma(1, z(n)), (n, 1, Nb))",
        symbols=_sym("n", "Nb"),
        functions=["v", "z"],
        difficulty=3,
        provenance="author-constructed transport spectral kernel",
        ladder_id="generic_sum_fold",
    ),
    dict(
        id="C-scattering-pw",
        family="scattering",
        current=(
            "Piecewise((T(n, m), Ne(n, m)), (0, True)) + "
            "Piecewise((T(n, m), Ne(n, m)), (0, True))"
        ),
        target_compact="Piecewise((2*T(n, m), Ne(n, m)), (0, True))",
        symbols=_sym("n", "m"),
        functions=["T"],
        difficulty=3,
        provenance="author-constructed off-diagonal scattering Piecewise",
        ladder_id="generic_sum_fold",
    ),
    dict(
        id="C-diagram-triple",
        family="diagrammatic",
        current=(
            "Sum(V(n, m, ell)*G(n)*G(m)*G(ell), (n, 1, Nb), (m, 1, Nb), (ell, 1, Nb)) + "
            "Sum(V(n, m, ell)*G(n)*G(m)*G(ell), (n, 1, Nb), (m, 1, Nb), (ell, 1, Nb))"
        ),
        target_compact=(
            "2*Sum(V(n, m, ell)*G(n)*G(m)*G(ell), (n, 1, Nb), (m, 1, Nb), (ell, 1, Nb))"
        ),
        symbols=_sym("n", "m", "ell", "Nb"),
        functions=["V", "G"],
        difficulty=4,
        provenance="author-constructed three-point diagrammatic sum",
        ladder_id="generic_sum_fold",
    ),
]


def _accept_identity(seed: dict) -> tuple[bool, str, object]:
    r = _verify(seed["current"], seed["candidate"], seed["symbols"],
                seed.get("functions"))
    wanted = seed.get("expected_verdict", ZERO)
    if wanted is None:
        return True, r.verdict, r
    return r.verdict == wanted, r.verdict, r


def write_item(item: dict, bench: Path) -> Path:
    tier = item["tier"].lower()
    split = item["split"]
    path = bench / split / f"tier_{tier}" / f"{item['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n")
    return path


def main() -> int:
    bench = ROOT / "benchmark"
    kept: list[dict] = []
    skipped: list[dict] = []

    print("Validating Tier A identities...")
    for seed in IDENTITIES:
        ok, verdict, result = _accept_identity({**seed, "expected_verdict": ZERO})
        if not ok:
            # keep as UNKNOWN-labelled if the engine honestly cannot prove it
            if verdict == UNKNOWN:
                item = make_item(
                    tier="A", task="adjudicate", expected_verdict=UNKNOWN,
                    provenance="generated identity; engine UNKNOWN (not relabelled ZERO)",
                    **{k: seed[k] for k in seed if k != "notes"},
                    notes=seed.get("notes", "") + f"; actual={verdict}",
                )
                kept.append(item)
                print(f"  KEEP-as-UNKNOWN {seed['id']} ({result.seconds}s)")
            else:
                skipped.append({"id": seed["id"], "wanted": ZERO, "got": verdict})
                print(f"  SKIP {seed['id']} wanted ZERO got {verdict}")
            continue
        item = make_item(
            tier="A", task="adjudicate", expected_verdict=ZERO,
            provenance="generated exact identity; engine-confirmed ZERO",
            **{k: seed[k] for k in seed if k != "notes"},
            notes=seed.get("notes", ""),
        )
        kept.append(item)
        print(f"  ZERO {seed['id']} ({result.seconds:.3f}s)")
        for mut in mutate(seed):
            r = _verify(mut["current"], mut["candidate"], mut["symbols"],
                        mut.get("functions"))
            if r.verdict == ZERO:
                skipped.append({"id": mut["id"], "reason": "mutation still ZERO"})
                print(f"  SKIP mutation still ZERO {mut['id']}")
                continue
            expected = NONZERO if r.verdict == NONZERO else UNKNOWN
            mut_fields = {k: v for k, v in mut.items()
                          if k != "expected_verdict"}
            item = make_item(
                tier="A", task="adjudicate", expected_verdict=expected,
                provenance="controlled corruption of an engine-confirmed identity",
                **mut_fields,
                notes=f"actual_verdict={r.verdict}",
            )
            kept.append(item)
            print(f"  {r.verdict:8} {mut['id']}")

    for seed in UNKNOWN_SEEDS:
        r = _verify(seed["current"], seed["candidate"], seed["symbols"],
                    seed.get("functions"))
        expected = seed["expected_verdict"]
        if r.verdict != expected:
            # store actual, do not relabel
            print(f"  retarget {seed['id']}: wanted {expected} got {r.verdict}")
            expected = r.verdict
        item = make_item(
            tier="A", task="adjudicate", expected_verdict=expected,
            provenance="adversarial / assumption-sensitive case",
            **{k: seed[k] for k in seed if k not in {"expected_verdict", "notes"}},
            notes=seed.get("notes", ""),
        )
        kept.append(item)

    print("Validating Tier B compactification golds...")
    for seed in TIER_B:
        r = _verify(seed["current"], seed["target_compact"], seed["symbols"],
                    seed.get("functions"))
        if r.verdict != ZERO:
            skipped.append({"id": seed["id"], "wanted": ZERO, "got": r.verdict})
            print(f"  SKIP B {seed['id']} gold not ZERO ({r.verdict})")
            continue
        item = make_item(
            tier="B", task="compactify",
            provenance="curated equivalent pair; gold hidden from proposer",
            human_reference=seed["target_compact"],
            **{k: seed[k] for k in seed},
        )
        kept.append(item)
        print(f"  B ZERO {seed['id']}")

    print("Preparing Tier C...")
    long_src = ROOT / "examples/long/Guo_Sigma_abc_dc_exact.txt"
    for seed in TIER_C:
        payload = dict(seed)
        if payload.get("id") == "C-guo-sigma-abc":
            payload["current"] = (
                "WOLFRAM_SOURCE_FILE:" + payload["source_file"]
            )
            payload["notes"] = seed["notes"]
            item = make_item(
                tier="C", task="compactify",
                **{k: payload[k] for k in payload},
            )
            item["split"] = "dev"
            kept.append(item)
            print(f"  C flagship (dev, contaminated) {item['id']} "
                  f"bytes={long_src.stat().st_size}")
            continue
        gold = payload.get("target_compact")
        if gold:
            r = _verify(payload["current"], gold, payload["symbols"],
                        payload.get("functions"))
            if r.verdict != ZERO:
                skipped.append({"id": payload["id"], "got": r.verdict})
                print(f"  SKIP C {payload['id']} gold {r.verdict}")
                continue
            print(f"  C ZERO {payload['id']}")
        else:
            print(f"  C no-gold {payload['id']}")
        item = make_item(
            tier="C", task="compactify",
            human_reference=gold,
            **{k: payload[k] for k in payload if k != "target_compact"},
            target_compact=gold,
        )
        kept.append(item)

    # wipe previous generated json items (not README/schema)
    for split in ("dev", "test"):
        for tier in ("tier_a", "tier_b", "tier_c"):
            d = bench / split / tier
            d.mkdir(parents=True, exist_ok=True)
            for p in d.glob("*.json"):
                p.unlink()

    meta_rows = []
    for item in kept:
        path = write_item(item, bench)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        meta_rows.append({
            "id": item["id"],
            "tier": item["tier"],
            "split": item["split"],
            "family": item["family"],
            "task": item["task"],
            "expected_verdict": item.get("expected_verdict") or "",
            "mutation_type": item.get("mutation_type") or "",
            "difficulty": item["difficulty"],
            "sha256": digest,
            "path": str(path.relative_to(ROOT)),
        })

    meta_path = bench / "metadata.csv"
    with meta_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(meta_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sorted(meta_rows, key=lambda r: r["id"]))

    manifest = {
        "version": VERSION,
        "n_items": len(kept),
        "n_skipped": len(skipped),
        "counts_by_split": {},
        "counts_by_tier": {},
        "skipped": skipped,
        "item_sha256": {row["id"]: row["sha256"] for row in meta_rows},
    }
    for row in meta_rows:
        manifest["counts_by_split"][row["split"]] = (
            manifest["counts_by_split"].get(row["split"], 0) + 1)
        manifest["counts_by_tier"][row["tier"]] = (
            manifest["counts_by_tier"].get(row["tier"], 0) + 1)
    (bench / "validation" / "freeze_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest["counts_by_tier"] | {"split": manifest["counts_by_split"],
                                                   "skipped": len(skipped)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
