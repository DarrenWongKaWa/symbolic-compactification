"""Build ssc-structure-bench-v0.1. Does not touch ssc-bench-v0.1/v0.2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

VERSION = "ssc-structure-bench-v0.1"
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "benchmark_structure" / VERSION

CTX_GENERIC = [
    "Exact scientific expression. Repeated subexpressions may be reusable kernels.",
    "Index permutations may form orbits. Several specializations of one function "
    "may share a master object. Apparent merges can be false.",
]
CTX_RESPONSE = CTX_GENERIC + [
    "Linear-response style object. Repeated denominators may be response kernels.",
]
CTX_GREEN = CTX_GENERIC + [
    "Green-function / spectral object. Resolvent structure may repeat.",
]
CTX_THERMAL = CTX_GENERIC + [
    "Thermal / Matsubara-style object. Shared analytic masters may exist.",
]
CTX_TENSOR = CTX_GENERIC + [
    "Indexed tensor expression. Permutation of indices may expose a generator.",
]


def S(*names):
    return [{"name": n, "real": True} for n in names]


def item(**kwargs) -> dict:
    rec = {
        "version": VERSION,
        "task": "structure_discovery",
        "source_format": "sympy",
        "assumptions": kwargs.pop("assumptions", []),
        "scientific_context": kwargs.pop("scientific_context", CTX_GENERIC),
        "hidden_from_proposer": True,
        "license": "author-constructed CC-BY-4.0 for this benchmark",
    }
    rec.update(kwargs)
    rec.setdefault("gold_auxiliaries", rec.get("hidden_gold", {}).get("aux_names", []))
    return rec


def all_items() -> list[dict]:
    items = []

    # ----- DEV S1 positive -----
    items.append(item(
        id="S1-pos-kernel-mul", split="dev", tier="S1", polarity="positive",
        family="algebra", domain="synthetic",
        abstraction_level="D2",
        current="K(n)*a(n) + K(n)*b(n)",
        symbols=S("n"), functions=["K", "a", "b"],
        gold_types=["repeated_kernel"],
        gold_hypothesis_type="repeated_kernel",
        gold_target_subexpressions=["K(n)"],
        gold_reconstruction="K(n)*(a(n) + b(n))",
        hidden_gold={"kind": "repeated_kernel", "aux_names": ["Kchan"]},
        forbidden_types=[], forbidden_reconstructions=[],
        provenance="author-constructed exact identity",
        downstream={"task": "count_kernels", "gold_answer": 1},
    ))
    items.append(item(
        id="S1-pos-kernel-sum", split="dev", tier="S1", polarity="positive",
        family="algebra", domain="synthetic", abstraction_level="D2",
        current="Sum(K(n)*a(n),(n,1,N)) + Sum(K(n)*b(n),(n,1,N))",
        symbols=S("n", "N"), functions=["K", "a", "b"],
        gold_types=["repeated_kernel", "structural_regrouping"],
        gold_hypothesis_type="repeated_kernel",
        gold_target_subexpressions=["K(n)"],
        gold_reconstruction="Sum(K(n)*(a(n) + b(n)),(n,1,N))",
        hidden_gold={"kind": "repeated_kernel", "aux_names": ["Ksum"]},
        provenance="author-constructed sum identity",
    ))
    items.append(item(
        id="S1-pos-orbit-swap", split="dev", tier="S1", polarity="positive",
        family="symmetry", domain="synthetic", abstraction_level="D5",
        current="F(n, m) + F(m, n)",
        symbols=S("n", "m"), functions=["F"],
        gold_types=["permutation_orbit", "symmetry_invariant", "tensor_generator"],
        gold_hypothesis_type="permutation_orbit",
        gold_target_subexpressions=["F(n, m)", "F(m, n)"],
        gold_reconstruction="F(n, m) + F(m, n)",
        hidden_gold={"kind": "permutation_orbit", "aux_names": ["Forbit"]},
        scientific_context=CTX_TENSOR,
        downstream={"task": "index_swap", "pair": ["n", "m"], "gold_answer": "invariant"},
        provenance="author-constructed swap orbit",
    ))
    items.append(item(
        id="S1-pos-master-spec", split="dev", tier="S1", polarity="positive",
        family="analytic", domain="synthetic", abstraction_level="D3",
        current="G(a) + G(b) + G(c)",
        symbols=S("a", "b", "c"), functions=["G"],
        gold_types=["master_function"],
        gold_hypothesis_type="master_function",
        gold_target_subexpressions=["G(a)", "G(b)", "G(c)"],
        gold_reconstruction="G(a) + G(b) + G(c)",
        hidden_gold={"kind": "master_function", "aux_names": ["Gmaster"]},
        provenance="author-constructed master specializations",
    ))
    items.append(item(
        id="S1-pos-dd", split="dev", tier="S1", polarity="positive",
        family="analytic", domain="synthetic", abstraction_level="D4",
        current="(f(x) - f(y))/(x - y)",
        symbols=S("x", "y"), functions=["f"],
        gold_types=["divided_difference"],
        gold_hypothesis_type="divided_difference",
        gold_target_subexpressions=["(f(x) - f(y))/(x - y)"],
        gold_reconstruction="(f(x) - f(y))/(x - y)",
        hidden_gold={"kind": "divided_difference", "aux_names": ["DDf"]},
        provenance="author-constructed difference quotient",
    ))
    items.append(item(
        id="S1-pos-spectral-two", split="dev", tier="S1", polarity="positive",
        family="green", domain="synthetic", abstraction_level="D3",
        current="1/(z - e(1)) + 1/(z - e(2))",
        symbols=S("z"), functions=["e"],
        gold_types=["master_function", "spectral_family", "repeated_kernel"],
        gold_hypothesis_type="spectral_family",
        gold_target_subexpressions=["1/(z - e(1))", "1/(z - e(2))"],
        hidden_gold={"kind": "spectral_family", "aux_names": ["Resz"]},
        scientific_context=CTX_GREEN,
        provenance="author-constructed two-pole resolvent",
    ))
    items.append(item(
        id="S1-pos-pw-same", split="dev", tier="S1", polarity="positive",
        family="analytic", domain="synthetic", abstraction_level="D4",
        current="Piecewise((q, n > 0), (q, True))",
        symbols=S("q", "n"), functions=[],
        gold_types=["confluent_representation"],
        gold_hypothesis_type="confluent_representation",
        gold_target_subexpressions=["q"],
        gold_reconstruction="q",
        hidden_gold={"kind": "confluent_representation", "aux_names": ["Ubranch"]},
        provenance="author-constructed identical-branch Piecewise",
    ))
    items.append(item(
        id="S1-pos-derivative", split="dev", tier="S1", polarity="positive",
        family="special", domain="synthetic", abstraction_level="D3",
        current="polygamma(0, z) + polygamma(1, z)",
        symbols=S("z"), functions=[],
        gold_types=["derivative_family"],
        gold_hypothesis_type="derivative_family",
        gold_target_subexpressions=["polygamma(0, z)", "polygamma(1, z)"],
        hidden_gold={"kind": "derivative_family", "aux_names": ["PsiFam"]},
        provenance="author-constructed polygamma family",
    ))

    # ----- DEV S1 negative -----
    items.append(item(
        id="S1-neg-poles-distinct", split="dev", tier="S1", polarity="negative",
        family="algebra", domain="synthetic", abstraction_level="D2",
        current="1/(x - a) + 1/(x - a - d)",
        symbols=S("x", "a", "d"), functions=[],
        gold_types=[],
        forbidden_types=[],  # master_function is allowed; identical merge is not
        forbidden_reconstructions=["2/(x - a)", "2*(1/(x - a))", "2/ (x - a)"],
        gold_hypothesis_type=None,
        hidden_gold={"kind": "distinct_poles", "aux_names": []},
        provenance="visually similar poles that must not collapse",
    ))
    items.append(item(
        id="S1-neg-broken-orbit", split="dev", tier="S1", polarity="negative",
        family="symmetry", domain="synthetic", abstraction_level="D5",
        current="F(n, m) + 2*F(m, n)",
        symbols=S("n", "m"), functions=["F"],
        gold_types=[],
        forbidden_reconstructions=["F(n, m) + F(m, n)"],
        gold_hypothesis_type=None,
        scientific_context=CTX_TENSOR,
        hidden_gold={"kind": "broken_orbit", "aux_names": []},
        downstream={"task": "index_swap", "pair": ["n", "m"], "gold_answer": "changes"},
        provenance="coefficients break the equal-weight orbit",
    ))
    items.append(item(
        id="S1-neg-pw-not-abs", split="dev", tier="S1", polarity="negative",
        family="analytic", domain="synthetic", abstraction_level="D4",
        current="Piecewise((x, x > 0), (-x - 1, True))",
        symbols=S("x"), functions=[],
        gold_types=[],
        forbidden_reconstructions=["x", "-x", "Abs(x)"],
        hidden_gold={"kind": "invalid_branch_merge", "aux_names": []},
        provenance="branches are not a single Abs or sign object",
    ))
    items.append(item(
        id="S1-neg-fake-master", split="dev", tier="S1", polarity="negative",
        family="analytic", domain="synthetic", abstraction_level="D3",
        current="F(x) + G(x) + H(x)",
        symbols=S("x"), functions=["F", "G", "H"],
        gold_types=[],
        forbidden_types=["master_function"],
        forbidden_reconstructions=["3*F(x)"],
        hidden_gold={"kind": "independent_functions", "aux_names": []},
        provenance="three distinct functions; no shared master",
    ))

    # ----- DEV S2 -----
    items.append(item(
        id="S2-pos-kubo-double", split="dev", tier="S2", polarity="positive",
        family="kubo_response", domain="response", abstraction_level="D2",
        current=(
            "Sum(v(n, m)*v(m, n)/(eps(n) - eps(m) + I*eta), (n, 1, Nb), (m, 1, Nb))"
            " + Sum(w(n, m)*w(m, n)/(eps(n) - eps(m) + I*eta), (n, 1, Nb), (m, 1, Nb))"
        ),
        symbols=S("n", "m", "Nb", "eta"), functions=["v", "w", "eps"],
        gold_types=["repeated_kernel", "permutation_orbit"],
        gold_hypothesis_type="repeated_kernel",
        gold_target_subexpressions=["1/(eps(n) - eps(m) + I*eta)"],
        gold_reconstruction=None,
        scientific_context=CTX_RESPONSE,
        hidden_gold={"kind": "repeated_kernel", "aux_names": ["KuboK"]},
        provenance="author-constructed Kubo double-counting skeleton (not a paper dump)",
    ))
    items.append(item(
        id="S2-pos-green-resolvent", split="dev", tier="S2", polarity="positive",
        family="green", domain="many_body", abstraction_level="D3",
        current="1/(w - eps(n) + I*eta) + 1/(w - eps(m) + I*eta)",
        symbols=S("w", "eta", "n", "m"), functions=["eps"],
        gold_types=["spectral_family", "master_function"],
        gold_hypothesis_type="spectral_family",
        gold_target_subexpressions=[
            "1/(w - eps(n) + I*eta)", "1/(w - eps(m) + I*eta)",
        ],
        scientific_context=CTX_GREEN,
        hidden_gold={"kind": "spectral_family", "aux_names": ["Gret"]},
        provenance="author-constructed retarded resolvent pair",
    ))
    items.append(item(
        id="S2-pos-thermal-pair", split="dev", tier="S2", polarity="positive",
        family="thermal", domain="thermal", abstraction_level="D3",
        current="A*polygamma(0, zP) + A*polygamma(0, zM)",
        symbols=S("A", "zP", "zM"), functions=[],
        gold_types=["repeated_kernel", "master_function", "derivative_family"],
        gold_hypothesis_type="repeated_kernel",
        gold_target_subexpressions=["A"],
        gold_reconstruction="A*(polygamma(0, zP) + polygamma(0, zM))",
        scientific_context=CTX_THERMAL,
        hidden_gold={"kind": "repeated_kernel", "aux_names": ["PhiTh"]},
        provenance="author-constructed thermal polygamma pair (not a Fermi closed form)",
    ))
    items.append(item(
        id="S2-pos-tensor-orbit", split="dev", tier="S2", polarity="positive",
        family="tensor", domain="geometry", abstraction_level="D5",
        current="T(i, j)*v(i)*v(j) + T(j, i)*v(j)*v(i)",
        symbols=S("i", "j"), functions=["T", "v"],
        gold_types=["permutation_orbit", "symmetry_invariant"],
        gold_hypothesis_type="permutation_orbit",
        gold_target_subexpressions=["T(i, j)", "T(j, i)"],
        scientific_context=CTX_TENSOR,
        hidden_gold={"kind": "permutation_orbit", "aux_names": ["Tgen"]},
        provenance="author-constructed symmetric tensor contraction",
        downstream={"task": "index_swap", "pair": ["i", "j"], "gold_answer": "invariant"},
    ))
    items.append(item(
        id="S2-neg-channel-gamma", split="dev", tier="S2", polarity="negative",
        family="kubo_response", domain="response", abstraction_level="D2",
        current=(
            "1/(eps(n) - eps(m) + I*eta) + 1/(eps(n) - eps(m) + I*Gamma)"
        ),
        symbols=S("n", "m", "eta", "Gamma"), functions=["eps"],
        gold_types=[],
        forbidden_reconstructions=[
            "2/(eps(n) - eps(m) + I*eta)",
            "2*(1/(eps(n) - eps(m) + I*eta))",
        ],
        scientific_context=CTX_RESPONSE,
        hidden_gold={"kind": "distinct_broadening", "aux_names": []},
        provenance="two physically distinct broadening parameters",
    ))
    items.append(item(
        id="S2-pos-perturbation", split="dev", tier="S2", polarity="positive",
        family="perturbation", domain="many_body", abstraction_level="D2",
        current="V(p)*G0(p)*V(p) + V(q)*G0(q)*V(q)",
        symbols=S("p", "q"), functions=["V", "G0"],
        gold_types=["master_function", "repeated_kernel"],
        gold_hypothesis_type="master_function",
        gold_target_subexpressions=["V(p)*G0(p)*V(p)", "V(q)*G0(q)*V(q)"],
        hidden_gold={"kind": "master_function", "aux_names": ["SigmaBorn"]},
        provenance="author-constructed Born-like self-energy skeleton",
    ))

    # ----- DEV S3 (author-constructed physics-shaped; not paper dumps) -----
    items.append(item(
        id="S3-pos-transport-kernel", split="dev", tier="S3", polarity="positive",
        family="transport", domain="transport", abstraction_level="D2",
        current=(
            "Sum(vx(n)*vx(n)*(-diff(n))/(w - eps(n) + I*eta), (n, 1, Nb))"
            " + Sum(vy(n)*vy(n)*(-diff(n))/(w - eps(n) + I*eta), (n, 1, Nb))"
        ),
        symbols=S("n", "Nb", "w", "eta"), functions=["vx", "vy", "diff", "eps"],
        gold_types=["repeated_kernel", "structural_regrouping"],
        gold_hypothesis_type="repeated_kernel",
        gold_target_subexpressions=["1/(w - eps(n) + I*eta)"],
        scientific_context=CTX_RESPONSE,
        hidden_gold={"kind": "repeated_kernel", "aux_names": ["Ktr"]},
        provenance="author-constructed conductivity-kernel skeleton",
    ))
    items.append(item(
        id="S3-pos-scattering-kernel", split="dev", tier="S3", polarity="positive",
        family="scattering", domain="scattering", abstraction_level="D2",
        current="M(k, p)*M(p, k)/(En - e(p) + I*eta) + M(k, q)*M(q, k)/(En - e(q) + I*eta)",
        symbols=S("k", "p", "q", "En", "eta"), functions=["M", "e"],
        gold_types=["master_function", "spectral_family"],
        gold_hypothesis_type="master_function",
        gold_target_subexpressions=[
            "M(k, p)*M(p, k)/(En - e(p) + I*eta)",
            "M(k, q)*M(q, k)/(En - e(q) + I*eta)",
        ],
        scientific_context=CTX_GREEN,
        hidden_gold={"kind": "master_function", "aux_names": ["T2nd"]},
        provenance="author-constructed second-order scattering skeleton",
    ))
    items.append(item(
        id="S3-pos-matsubara-pair", split="dev", tier="S3", polarity="positive",
        family="thermal", domain="thermal", abstraction_level="D2",
        current="1/(I*wn - xi) + 1/(-I*wn - xi)",
        symbols=S("wn", "xi"), functions=[],
        gold_types=["repeated_kernel", "master_function"],
        gold_hypothesis_type="master_function",
        gold_target_subexpressions=["1/(I*wn - xi)", "1/(-I*wn - xi)"],
        scientific_context=CTX_THERMAL,
        hidden_gold={"kind": "master_function", "aux_names": ["Gmat"]},
        provenance="author-constructed Matsubara pair (not a summation identity)",
    ))

    # ----- HELD-OUT TEST (frozen; different expressions) -----
    items.append(item(
        id="T-S1-pos-kernel-triple", split="test", tier="S1", polarity="positive",
        family="algebra", domain="synthetic", abstraction_level="D2",
        current="U(k)*p(k) + U(k)*q(k) + U(k)*r(k)",
        symbols=S("k"), functions=["U", "p", "q", "r"],
        gold_types=["repeated_kernel"],
        gold_hypothesis_type="repeated_kernel",
        gold_target_subexpressions=["U(k)"],
        gold_reconstruction="U(k)*(p(k) + q(k) + r(k))",
        hidden_gold={"kind": "repeated_kernel", "aux_names": ["Uker"]},
        provenance="held-out triple kernel",
    ))
    items.append(item(
        id="T-S1-pos-orbit", split="test", tier="S1", polarity="positive",
        family="symmetry", domain="synthetic", abstraction_level="D5",
        current="Q(a, b) + Q(b, a)",
        symbols=S("a", "b"), functions=["Q"],
        gold_types=["permutation_orbit", "symmetry_invariant"],
        gold_hypothesis_type="permutation_orbit",
        gold_target_subexpressions=["Q(a, b)", "Q(b, a)"],
        scientific_context=CTX_TENSOR,
        hidden_gold={"kind": "permutation_orbit", "aux_names": ["Qorb"]},
        downstream={"task": "index_swap", "pair": ["a", "b"], "gold_answer": "invariant"},
        provenance="held-out swap orbit",
    ))
    items.append(item(
        id="T-S1-pos-master", split="test", tier="S1", polarity="positive",
        family="analytic", domain="synthetic", abstraction_level="D3",
        current="H(u) + H(v) + H(w)",
        symbols=S("u", "v", "w"), functions=["H"],
        gold_types=["master_function"],
        gold_hypothesis_type="master_function",
        gold_target_subexpressions=["H(u)", "H(v)", "H(w)"],
        hidden_gold={"kind": "master_function", "aux_names": ["Hmast"]},
        provenance="held-out master specializations",
    ))
    items.append(item(
        id="T-S1-pos-dd", split="test", tier="S1", polarity="positive",
        family="analytic", domain="synthetic", abstraction_level="D4",
        current="(s(p) - s(q))/(p - q)",
        symbols=S("p", "q"), functions=["s"],
        gold_types=["divided_difference"],
        gold_hypothesis_type="divided_difference",
        gold_target_subexpressions=["(s(p) - s(q))/(p - q)"],
        hidden_gold={"kind": "divided_difference", "aux_names": ["DDs"]},
        provenance="held-out difference quotient",
    ))
    items.append(item(
        id="T-S1-neg-poles", split="test", tier="S1", polarity="negative",
        family="algebra", domain="synthetic", abstraction_level="D2",
        current="1/(t - b) + 1/(t - b - c)",
        symbols=S("t", "b", "c"), functions=[],
        gold_types=[],
        forbidden_reconstructions=["2/(t - b)", "2*(1/(t - b))"],
        hidden_gold={"kind": "distinct_poles", "aux_names": []},
        provenance="held-out distinct poles",
    ))
    items.append(item(
        id="T-S1-neg-broken-orbit", split="test", tier="S1", polarity="negative",
        family="symmetry", domain="synthetic", abstraction_level="D5",
        current="R(x, y) + 3*R(y, x)",
        symbols=S("x", "y"), functions=["R"],
        gold_types=[],
        forbidden_reconstructions=["R(x, y) + R(y, x)"],
        scientific_context=CTX_TENSOR,
        hidden_gold={"kind": "broken_orbit", "aux_names": []},
        downstream={"task": "index_swap", "pair": ["x", "y"], "gold_answer": "changes"},
        provenance="held-out broken orbit",
    ))
    items.append(item(
        id="T-S2-pos-kubo-channels", split="test", tier="S2", polarity="positive",
        family="kubo_response", domain="response", abstraction_level="D2",
        current=(
            "Sum(jx(n)*jx(m)/(om - eps(n) + eps(m) + I*eta),(n,1,N),(m,1,N))"
            " + Sum(jy(n)*jy(m)/(om - eps(n) + eps(m) + I*eta),(n,1,N),(m,1,N))"
        ),
        symbols=S("n", "m", "N", "om", "eta"), functions=["jx", "jy", "eps"],
        gold_types=["repeated_kernel"],
        gold_hypothesis_type="repeated_kernel",
        gold_target_subexpressions=["1/(om - eps(n) + eps(m) + I*eta)"],
        scientific_context=CTX_RESPONSE,
        hidden_gold={"kind": "repeated_kernel", "aux_names": ["Kxy"]},
        provenance="held-out two-channel Kubo skeleton",
    ))
    items.append(item(
        id="T-S2-pos-green-two", split="test", tier="S2", polarity="positive",
        family="green", domain="many_body", abstraction_level="D3",
        current="1/(nu - xi(1) + I*eta) + 1/(nu - xi(2) + I*eta) + 1/(nu - xi(3) + I*eta)",
        symbols=S("nu", "eta"), functions=["xi"],
        gold_types=["spectral_family", "master_function"],
        gold_hypothesis_type="spectral_family",
        gold_target_subexpressions=[
            "1/(nu - xi(1) + I*eta)", "1/(nu - xi(2) + I*eta)", "1/(nu - xi(3) + I*eta)",
        ],
        scientific_context=CTX_GREEN,
        hidden_gold={"kind": "spectral_family", "aux_names": ["G3"]},
        provenance="held-out three-pole resolvent",
    ))
    items.append(item(
        id="T-S2-neg-pw", split="test", tier="S2", polarity="negative",
        family="analytic", domain="synthetic", abstraction_level="D4",
        current="Piecewise((K(x, y), Ne(x, y)), (L(x, x), True))",
        symbols=S("x", "y"), functions=["K", "L"],
        gold_types=[],
        forbidden_reconstructions=["K(x, y)", "L(x, x)"],
        hidden_gold={"kind": "invalid_branch_merge", "aux_names": []},
        provenance="held-out distinct-branch Piecewise",
    ))
    items.append(item(
        id="T-S3-pos-tensor", split="test", tier="S3", polarity="positive",
        family="tensor", domain="geometry", abstraction_level="D5",
        current="S(mu, nu)*p(mu)*p(nu) + S(nu, mu)*p(nu)*p(mu)",
        symbols=S("mu", "nu"), functions=["S", "p"],
        gold_types=["permutation_orbit", "symmetry_invariant"],
        gold_hypothesis_type="permutation_orbit",
        gold_target_subexpressions=["S(mu, nu)", "S(nu, mu)"],
        scientific_context=CTX_TENSOR,
        hidden_gold={"kind": "permutation_orbit", "aux_names": ["Sgen"]},
        provenance="held-out symmetric bilinear form",
        downstream={"task": "index_swap", "pair": ["mu", "nu"], "gold_answer": "invariant"},
    ))
    items.append(item(
        id="T-S3-pos-thermal", split="test", tier="S3", polarity="positive",
        family="thermal", domain="thermal", abstraction_level="D2",
        current="B*polygamma(0, zp) + B*polygamma(0, zm)",
        symbols=S("B", "zp", "zm"), functions=[],
        gold_types=["repeated_kernel"],
        gold_hypothesis_type="repeated_kernel",
        gold_target_subexpressions=["B"],
        gold_reconstruction="B*(polygamma(0, zp) + polygamma(0, zm))",
        scientific_context=CTX_THERMAL,
        hidden_gold={"kind": "repeated_kernel", "aux_names": ["PhiB"]},
        provenance="held-out thermal factor",
    ))
    items.append(item(
        id="T-S1-neg-fake-master", split="test", tier="S1", polarity="negative",
        family="analytic", domain="synthetic", abstraction_level="D3",
        current="P(t) + Q(t) + R(t)",
        symbols=S("t"), functions=["P", "Q", "R"],
        gold_types=[],
        forbidden_types=["master_function"],
        forbidden_reconstructions=["3*P(t)"],
        hidden_gold={"kind": "independent_functions", "aux_names": []},
        provenance="held-out independent functions",
    ))
    return items


def write_benchmark() -> dict:
    items = all_items()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dev").mkdir(exist_ok=True)
    (OUT / "test").mkdir(exist_ok=True)
    (OUT / "validation").mkdir(exist_ok=True)
    hashes = {}
    for it in items:
        split = it["split"]
        path = OUT / split / f"{it['id']}.json"
        text = json.dumps(it, indent=2, sort_keys=True) + "\n"
        path.write_text(text)
        hashes[it["id"]] = hashlib.sha256(text.encode()).hexdigest()
    meta = {
        "version": VERSION,
        "n": len(items),
        "n_dev": sum(i["split"] == "dev" for i in items),
        "n_test": sum(i["split"] == "test" for i in items),
        "n_positive": sum(i["polarity"] == "positive" for i in items),
        "n_negative": sum(i["polarity"] == "negative" for i in items),
        "tiers": sorted({i["tier"] for i in items}),
        "guo_in_test": False,
        "note": "Guo is a DEV case study loaded from examples/long, not a test item.",
    }
    (OUT / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    freeze = {
        "version": VERSION,
        "n": len(items),
        "sha256_by_id": hashes,
        "frozen": False,  # set True by freeze step after DEV
    }
    (OUT / "validation" / "freeze_manifest.json").write_text(
        json.dumps(freeze, indent=2) + "\n"
    )
    return meta


if __name__ == "__main__":
    print(json.dumps(write_benchmark(), indent=2))
