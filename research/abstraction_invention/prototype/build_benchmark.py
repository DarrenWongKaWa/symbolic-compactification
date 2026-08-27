"""ssc-abstraction-bench-v0.1 — non-identical related structure.

Does not overwrite ssc-structure-bench-v0.1. Guo is not a test item.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

VERSION = "ssc-abstraction-bench-v0.1"
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "benchmark_abstraction" / VERSION

CTX = [
    "Subexpressions may share a parameterized mathematical object even when "
    "they are not syntactically identical.",
    "Propose a template and instance maps. Do not propose a final compact formula.",
    "Do not invent a shared object for unrelated terms.",
]


def S(*names):
    return [{"name": n, "real": True} for n in names]


def item(**kwargs) -> dict:
    rec = {
        "version": VERSION,
        "task": "abstraction_invention",
        "source_format": "sympy",
        "scientific_context": kwargs.pop("scientific_context", CTX),
        "hidden_from_proposer": True,
        "license": "author-constructed",
    }
    rec.update(kwargs)
    return rec


def all_items() -> list[dict]:
    items = []
    # ----- Family A anti-unification (B9 exact-srepr should miss) -----
    items.append(item(
        id="A-pos-born", split="dev", family="A_antiunification", polarity="positive",
        gold_operator="antiunification",
        current="V(p)*G0(p)*V(p) + V(q)*G0(q)*V(q)",
        symbols=S("p", "q"), functions=["V", "G0"],
        gold_members=["V(p)*G0(p)*V(p)", "V(q)*G0(q)*V(q)"],
        gold_template="V(theta0)*G0(theta0)*V(theta0)",
        hidden_gold={"aux_names": ["Fborn"]},
        provenance="Born-like self-energy; DEV miss of structure-discovery v0.1",
    ))
    items.append(item(
        id="A-pos-resolvent-weight", split="dev", family="A_antiunification",
        polarity="positive", gold_operator="antiunification",
        current="v(n)/(w - eps(n)) + v(m)/(w - eps(m))",
        symbols=S("n", "m", "w"), functions=["v", "eps"],
        gold_members=["v(n)/(w - eps(n))", "v(m)/(w - eps(m))"],
        gold_template="v(theta0)/(w - eps(theta0))",
        hidden_gold={"aux_names": ["Rweight"]},
        provenance="weighted resolvent specializations",
    ))
    items.append(item(
        id="A-pos-quad", split="dev", family="A_antiunification", polarity="positive",
        gold_operator="antiunification",
        current="(x - a)*(x - b) + (y - a)*(y - b)",
        symbols=S("x", "y", "a", "b"), functions=[],
        gold_members=["(x - a)*(x - b)", "(y - a)*(y - b)"],
        gold_template="(theta0 - a)*(theta0 - b)",
        hidden_gold={"aux_names": ["Qab"]},
        provenance="shared quadratic factors, different free variable",
    ))
    items.append(item(
        id="A-neg-unrelated", split="dev", family="A_antiunification", polarity="negative",
        gold_operator="antiunification",
        current="V(p)*G0(p)*V(p) + W(q)*H0(q)*W(q)",
        symbols=S("p", "q"), functions=["V", "G0", "W", "H0"],
        gold_members=[],
        forbidden_operators=["antiunification"],
        hidden_gold={"aux_names": []},
        provenance="different channels; no shared template that keeps function names",
    ))
    items.append(item(
        id="A-pos-three", split="dev", family="A_antiunification", polarity="positive",
        gold_operator="antiunification",
        current="V(p)*G0(p)*V(p) + V(q)*G0(q)*V(q) + V(r)*G0(r)*V(r)",
        symbols=S("p", "q", "r"), functions=["V", "G0"],
        gold_members=["V(p)*G0(p)*V(p)", "V(q)*G0(q)*V(q)"],
        gold_template="V(theta0)*G0(theta0)*V(theta0)",
        hidden_gold={"aux_names": ["F3"]},
        provenance="three specializations of one Born kernel",
    ))

    # ----- Family B master / derivative -----
    items.append(item(
        id="B-pos-poly-deriv", split="dev", family="B_master", polarity="positive",
        gold_operator="master_derivative",
        current="polygamma(0, z) + polygamma(1, z)",
        symbols=S("z"), functions=[],
        gold_members=["polygamma(0, z)", "polygamma(1, z)"],
        hidden_gold={"aux_names": ["Psi"]},
        provenance="derivative family; parser has polygamma not Derivative",
    ))
    items.append(item(
        id="B-neg-independent", split="dev", family="B_master", polarity="negative",
        gold_operator="master_derivative",
        current="F(x) + G(x)",
        symbols=S("x"), functions=["F", "G"],
        gold_members=[],
        forbidden_operators=["master_derivative"],
        hidden_gold={"aux_names": []},
        provenance="independent functions, no derivative relation",
    ))

    # ----- Family C confluence via specialization, not identical values -----
    items.append(item(
        id="C-pos-kernel-degen", split="dev", family="C_confluence", polarity="positive",
        gold_operator="confluence",
        current="Piecewise((K(n, m), Ne(n, m)), (K(n, n), True))",
        symbols=S("n", "m"), functions=["K"],
        gold_members=["K(n, m)", "K(n, n)"],
        gold_template="K(n, theta0)",
        hidden_gold={"aux_names": ["Kfam"]},
        provenance="degenerate branch is a specialization, not an equal value",
    ))
    items.append(item(
        id="C-neg-unrelated-pw", split="dev", family="C_confluence", polarity="negative",
        gold_operator="confluence",
        current="Piecewise((K(n, m), Ne(n, m)), (L(n, n), True))",
        symbols=S("n", "m"), functions=["K", "L"],
        gold_members=[],
        forbidden_operators=["confluence"],
        hidden_gold={"aux_names": []},
        provenance="distinct heads; not one confluent family",
    ))

    # ----- Family D parameterized generator family -----
    items.append(item(
        id="D-pos-bilinear", split="dev", family="D_basis", polarity="positive",
        gold_operator="antiunification",
        current="F(i, j)*v(i)*v(j) + F(j, k)*v(j)*v(k)",
        symbols=S("i", "j", "k"), functions=["F", "v"],
        gold_members=["F(i, j)*v(i)*v(j)", "F(j, k)*v(j)*v(k)"],
        gold_template="F(theta0, theta1)*v(theta0)*v(theta1)",
        hidden_gold={"aux_names": ["Gbil"]},
        provenance="two contractions of one bilinear generator",
    ))

    # ----- held-out TEST (different symbols) -----
    items.append(item(
        id="T-A-pos-born", split="test", family="A_antiunification", polarity="positive",
        gold_operator="antiunification",
        current="U(s)*D0(s)*U(s) + U(t)*D0(t)*U(t)",
        symbols=S("s", "t"), functions=["U", "D0"],
        gold_members=["U(s)*D0(s)*U(s)", "U(t)*D0(t)*U(t)"],
        hidden_gold={"aux_names": ["Fhat"]},
        provenance="held-out Born template",
    ))
    items.append(item(
        id="T-A-pos-weight", split="test", family="A_antiunification", polarity="positive",
        gold_operator="antiunification",
        current="j(a)/(om - xi(a)) + j(b)/(om - xi(b))",
        symbols=S("a", "b", "om"), functions=["j", "xi"],
        gold_members=["j(a)/(om - xi(a))", "j(b)/(om - xi(b))"],
        hidden_gold={"aux_names": ["Jw"]},
        provenance="held-out weighted resolvent",
    ))
    items.append(item(
        id="T-A-neg-unrelated", split="test", family="A_antiunification", polarity="negative",
        gold_operator="antiunification",
        current="U(s)*D0(s)*U(s) + Z(t)*Y0(t)*Z(t)",
        symbols=S("s", "t"), functions=["U", "D0", "Z", "Y0"],
        gold_members=[],
        forbidden_operators=["antiunification"],
        hidden_gold={"aux_names": []},
        provenance="held-out unrelated channels",
    ))
    items.append(item(
        id="T-B-neg-indep", split="test", family="B_master", polarity="negative",
        gold_operator="master_derivative",
        current="P(u) + Q(u)",
        symbols=S("u"), functions=["P", "Q"],
        gold_members=[],
        forbidden_operators=["master_derivative"],
        hidden_gold={"aux_names": []},
        provenance="held-out independent pair",
    ))
    items.append(item(
        id="T-C-pos-degen", split="test", family="C_confluence", polarity="positive",
        gold_operator="confluence",
        current="Piecewise((Q(x, y), Ne(x, y)), (Q(x, x), True))",
        symbols=S("x", "y"), functions=["Q"],
        gold_members=["Q(x, y)", "Q(x, x)"],
        hidden_gold={"aux_names": ["Qfam"]},
        provenance="held-out degenerate specialization",
    ))
    items.append(item(
        id="T-C-neg-pw", split="test", family="C_confluence", polarity="negative",
        gold_operator="confluence",
        current="Piecewise((Q(x, y), Ne(x, y)), (R(x, x), True))",
        symbols=S("x", "y"), functions=["Q", "R"],
        gold_members=[],
        forbidden_operators=["confluence"],
        hidden_gold={"aux_names": []},
        provenance="held-out unrelated branches",
    ))
    items.append(item(
        id="T-D-pos-bilin", split="test", family="D_basis", polarity="positive",
        gold_operator="antiunification",
        current="S(mu, nu)*p(mu)*p(nu) + S(nu, la)*p(nu)*p(la)",
        symbols=S("mu", "nu", "la"), functions=["S", "p"],
        gold_members=["S(mu, nu)*p(mu)*p(nu)", "S(nu, la)*p(nu)*p(la)"],
        hidden_gold={"aux_names": ["Sgen"]},
        provenance="held-out bilinear generator",
    ))
    items.append(item(
        id="T-A-pos-quad", split="test", family="A_antiunification", polarity="positive",
        gold_operator="antiunification",
        current="(u - c)*(u - d) + (w - c)*(w - d)",
        symbols=S("u", "w", "c", "d"), functions=[],
        gold_members=["(u - c)*(u - d)", "(w - c)*(w - d)"],
        hidden_gold={"aux_names": ["Qcd"]},
        provenance="held-out quadratic template",
    ))
    return items


def write_benchmark() -> dict:
    items = all_items()
    (OUT / "dev").mkdir(parents=True, exist_ok=True)
    (OUT / "test").mkdir(parents=True, exist_ok=True)
    (OUT / "validation").mkdir(exist_ok=True)
    hashes = {}
    for it in items:
        path = OUT / it["split"] / f"{it['id']}.json"
        text = json.dumps(it, indent=2, sort_keys=True) + "\n"
        path.write_text(text)
        hashes[it["id"]] = hashlib.sha256(text.encode()).hexdigest()
    meta = {
        "version": VERSION,
        "n": len(items),
        "n_dev": sum(i["split"] == "dev" for i in items),
        "n_test": sum(i["split"] == "test" for i in items),
        "guo_in_test": False,
        "note": "Items are deliberately non-identical. Frozen B9 should fail invention.",
    }
    (OUT / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    (OUT / "validation" / "freeze_manifest.json").write_text(
        json.dumps({"version": VERSION, "sha256_by_id": hashes, "frozen": False}, indent=2) + "\n"
    )
    return meta


if __name__ == "__main__":
    print(json.dumps(write_benchmark(), indent=2))
