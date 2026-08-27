"""ssc-abstraction-bench-v0.2-beyond-lgg. Does not overwrite v0.1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

VERSION = "ssc-abstraction-bench-v0.2-beyond-lgg"
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "benchmark_abstraction" / VERSION

CTX = [
    "Related expressions may be equivalent only after algebra, or related "
    "by an operator (derivative, permutation), not by leaf substitution.",
    "Do not emit a final compact formula. Propose F and operators.",
]


def S(*names):
    return [{"name": n, "real": True} for n in names]


def item(**kw):
    rec = {
        "version": VERSION, "task": "beyond_lgg", "source_format": "sympy",
        "scientific_context": CTX, "hidden_from_proposer": True,
        "license": "author-constructed",
    }
    rec.update(kw)
    return rec


def all_items():
    xs = []
    # T1 AC reordering
    xs.append(item(
        id="T1-pos-add-commute", split="dev", family="T1_ac", polarity="positive",
        gold_mode="algebraic_equivalence", expected_lgg_fail=True,
        current="(p + q)*u + (q + p)*v",
        symbols=S("p", "q", "u", "v"), functions=[],
        gold_members=["(p + q)*u", "(q + p)*v"],
        note="inner Add commutes; raw LGG may distort pairing",
        invalid_tempting="2*theta*u",
        abstraction_depth="F2",
        lgg_expected="shallow_or_miss",
    ))
    xs.append(item(
        id="T1-neg-different-sums", split="dev", family="T1_ac", polarity="negative",
        gold_mode="algebraic_equivalence", expected_lgg_fail=True,
        current="(p + q)*u + (p + r)*v",
        symbols=S("p", "q", "r", "u", "v"), functions=[],
        gold_members=[],
        note="p+q vs p+r are not AC-equal",
        abstraction_depth="F2",
    ))
    # T2 distributivity
    xs.append(item(
        id="T2-pos-distrib", split="dev", family="T2_distrib", polarity="positive",
        gold_mode="algebraic_equivalence", expected_lgg_fail=True,
        current="F(x*(y + z)) + F(x*y + x*z)",
        symbols=S("x", "y", "z"), functions=["F"],
        gold_members=["F(x*(y + z))", "F(x*y + x*z)"],
        note="Mul vs Add heads; LGG should be a hole; expand equalizes",
        abstraction_depth="F2",
        lgg_expected="miss",
    ))
    xs.append(item(
        id="T2-neg-not-distrib", split="dev", family="T2_distrib", polarity="negative",
        gold_mode="algebraic_equivalence", expected_lgg_fail=True,
        current="F(x*(y + z)) + F(x*y + w*z)",
        symbols=S("x", "y", "z", "w"), functions=["F"],
        gold_members=[],
        note="not the distributive identity",
        abstraction_depth="F2",
    ))
    # T3/T4 operator
    xs.append(item(
        id="T4-pos-pg-deriv", split="dev", family="T4_derivative", polarity="positive",
        gold_mode="operator", expected_lgg_fail=False,
        current="polygamma(0, z) + polygamma(1, z)",
        symbols=S("z"), functions=[],
        gold_members=["polygamma(0, z)", "polygamma(1, z)"],
        note="LGG may put a hole in the order; operator method must state d/dz",
        abstraction_depth="F3",
        lgg_expected="substitution_not_operator",
    ))
    xs.append(item(
        id="T4-neg-indep", split="dev", family="T4_derivative", polarity="negative",
        gold_mode="operator", expected_lgg_fail=True,
        current="F(z) + G(z)",
        symbols=S("z"), functions=["F", "G"],
        gold_members=[],
        abstraction_depth="F3",
    ))
    # T6 confluence-style specialization (LGG might work — control)
    xs.append(item(
        id="T6-pos-specialize", split="dev", family="T6_confluence", polarity="positive",
        gold_mode="confluence", expected_lgg_fail=False,
        current="Piecewise((K(n, m), Ne(n, m)), (K(n, n), True))",
        symbols=S("n", "m"), functions=["K"],
        gold_members=["K(n, m)", "K(n, n)"],
        abstraction_depth="F5",
        lgg_expected="may_succeed_parameterized",
    ))
    xs.append(item(
        id="T6-neg-heads", split="dev", family="T6_confluence", polarity="negative",
        gold_mode="confluence", expected_lgg_fail=True,
        current="Piecewise((K(n, m), Ne(n, m)), (L(n, n), True))",
        symbols=S("n", "m"), functions=["K", "L"],
        gold_members=[],
        abstraction_depth="F5",
    ))
    # T7 permutation as operator not F(theta,theta)
    xs.append(item(
        id="T7-pos-swap", split="dev", family="T7_basis", polarity="positive",
        gold_mode="operator", expected_lgg_fail=True,
        current="T(i, j) + T(j, i)",
        symbols=S("i", "j"), functions=["T"],
        gold_members=["T(i, j)", "T(j, i)"],
        note="LGG zip may yield T(theta,theta); permutation edge is the object",
        abstraction_depth="F3",
        lgg_expected="wrong_template",
    ))

    # held-out TEST
    xs.append(item(
        id="H-T2-pos-distrib", split="test", family="T2_distrib", polarity="positive",
        gold_mode="algebraic_equivalence", expected_lgg_fail=True,
        current="H(a*(b + c)) + H(a*b + a*c)",
        symbols=S("a", "b", "c"), functions=["H"],
        gold_members=["H(a*(b + c))", "H(a*b + a*c)"],
        abstraction_depth="F2",
    ))
    xs.append(item(
        id="H-T2-neg", split="test", family="T2_distrib", polarity="negative",
        gold_mode="algebraic_equivalence", expected_lgg_fail=True,
        current="H(a*(b + c)) + H(a*b + d*c)",
        symbols=S("a", "b", "c", "d"), functions=["H"],
        gold_members=[],
        abstraction_depth="F2",
    ))
    xs.append(item(
        id="H-T4-pos-pg", split="test", family="T4_derivative", polarity="positive",
        gold_mode="operator", expected_lgg_fail=False,
        current="polygamma(0, w) + polygamma(1, w)",
        symbols=S("w"), functions=[],
        gold_members=["polygamma(0, w)", "polygamma(1, w)"],
        abstraction_depth="F3",
    ))
    xs.append(item(
        id="H-T4-neg", split="test", family="T4_derivative", polarity="negative",
        gold_mode="operator", expected_lgg_fail=True,
        current="P(w) + Q(w)",
        symbols=S("w"), functions=["P", "Q"],
        gold_members=[],
        abstraction_depth="F3",
    ))
    xs.append(item(
        id="H-T1-pos-ac", split="test", family="T1_ac", polarity="positive",
        gold_mode="algebraic_equivalence", expected_lgg_fail=True,
        current="(s + t)*x + (t + s)*y",
        symbols=S("s", "t", "x", "y"), functions=[],
        gold_members=["(s + t)*x", "(t + s)*y"],
        abstraction_depth="F2",
    ))
    xs.append(item(
        id="H-T7-pos-swap", split="test", family="T7_basis", polarity="positive",
        gold_mode="operator", expected_lgg_fail=True,
        current="Q(a, b) + Q(b, a)",
        symbols=S("a", "b"), functions=["Q"],
        gold_members=["Q(a, b)", "Q(b, a)"],
        abstraction_depth="F3",
    ))
    return xs


def write():
    items = all_items()
    (OUT / "dev").mkdir(parents=True, exist_ok=True)
    (OUT / "test").mkdir(parents=True, exist_ok=True)
    (OUT / "validation").mkdir(exist_ok=True)
    hashes = {}
    for it in items:
        p = OUT / it["split"] / f"{it['id']}.json"
        t = json.dumps(it, indent=2, sort_keys=True) + "\n"
        p.write_text(t)
        hashes[it["id"]] = hashlib.sha256(t.encode()).hexdigest()
    meta = {
        "version": VERSION, "n": len(items),
        "n_dev": sum(i["split"] == "dev" for i in items),
        "n_test": sum(i["split"] == "test" for i in items),
        "guo_in_test": False,
        "frozen": False,
    }
    (OUT / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    (OUT / "validation" / "freeze_manifest.json").write_text(
        json.dumps({"sha256_by_id": hashes, "frozen": False, "version": VERSION}, indent=2) + "\n"
    )
    return meta


if __name__ == "__main__":
    print(json.dumps(write(), indent=2))
